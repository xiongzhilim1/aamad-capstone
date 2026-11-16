"""AI profile assistant: the author's free text becomes a draft they review (W21 to W23).

The raw text and the draft live only in an in-process store keyed by the session id. They
are never written to the database, never sent to the suggestion model, and are deleted on
accept, discard or sign-out (MN-013, MN-015, CR-009).
"""

import threading
import time
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.ai import controls
from app.ai.guardrails import check_draft
from app.ai.schemas import Checked, ProfileDraftOut
from app.api.deps import Actor
from app.api.errors import not_found
from app.api.schemas.profile import DraftAccept, DraftResponse, ProfileDraft
from app.crews import runtime
from app.domain import vocab
from app.domain.vocab import ProfileField
from app.services import people, policy

CREW = "profile_assistant"
TASK_ID = "draft_profile_v1"
DRAFT_TTL_SECONDS = 60 * 60


@dataclass
class _Held:
    text: str
    draft: ProfileDraft | None
    trace_id: str | None
    at: float


class DraftStore:
    """Session-held drafts (SAD §2). One per session; replaced by the next summarise."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._items: dict[str, _Held] = {}

    def put(self, sid: str, held: _Held) -> None:
        with self._lock:
            cutoff = time.monotonic() - DRAFT_TTL_SECONDS
            self._items = {k: v for k, v in self._items.items() if v.at > cutoff}
            self._items[sid] = held

    def get(self, sid: str) -> _Held | None:
        with self._lock:
            held = self._items.get(sid)
            if held and held.at <= time.monotonic() - DRAFT_TTL_SECONDS:
                del self._items[sid]
                return None
            return held

    def pop(self, sid: str) -> _Held | None:
        with self._lock:
            return self._items.pop(sid, None)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()


store = DraftStore()


def _values(enum: type) -> str:
    return ", ".join(e.value for e in enum)  # type: ignore[attr-defined]


def _inputs(text: str) -> dict[str, str]:
    """Only the author's own text and the fixed vocabulary: nothing about anyone else.
    Braces are replaced because CrewAI treats `{name}` in task text as a template variable."""
    return {
        "text": text.replace("{", "(").replace("}", ")"),
        "interests": _values(vocab.Interest),
        "challenges": _values(vocab.Challenge),
        "looking_for": _values(vocab.LookingFor),
        "industries": _values(vocab.Industry),
    }


def draft(db: Session, actor: Actor, text: str, trace_id: str) -> DraftResponse:
    """One model call per summarise action (MC-006). Saves nothing to the profile."""
    blocked = controls.preflight(db, actor.id, CREW)
    if blocked is not None:
        if blocked.code != "rate_limited":
            controls.write_trace(
                trace_id=trace_id, crew=CREW, user_id=actor.id, run=None, outcome="fallback",
                fallback_code=blocked.code, task_id=TASK_ID,
            )  # fmt: skip
        store.put(actor.session_id, _Held(text, None, None, time.monotonic()))
        return DraftResponse(
            status="fallback", source_text=text, fallback=blocked, trace_id=trace_id
        )

    def guard(out: ProfileDraftOut) -> Checked[ProfileDraft]:
        return check_draft(out, text)

    run = runtime.run_crew(TASK_ID, _inputs(text), ProfileDraftOut, guard)
    controls.breaker.record(run.failure is None)
    if run.failure is not None:
        code = controls.failure_code(run)
        controls.write_trace(
            trace_id=trace_id, crew=CREW, user_id=actor.id, run=run, outcome="fallback",
            fallback_code=code,
        )  # fmt: skip
        # The text is kept so the manual pickers open with the author's words still there.
        store.put(actor.session_id, _Held(text, None, None, time.monotonic()))
        return DraftResponse(
            status="fallback", source_text=text, fallback=controls.fallback(code), trace_id=trace_id
        )
    checked: Checked[ProfileDraft] = run.guarded
    d = checked.value
    tags = [*d.interests, *d.challenges, *d.looking_for, *([d.industry] if d.industry else [])]
    controls.write_trace(
        trace_id=trace_id, crew=CREW, user_id=actor.id, run=run, outcome="ok",
        output_ids=[t.value for t in tags], dropped=checked.dropped,
    )  # fmt: skip
    store.put(actor.session_id, _Held(text, d, trace_id, time.monotonic()))
    return DraftResponse(status="draft", draft=d, source_text=text, trace_id=trace_id)


def current(actor: Actor) -> DraftResponse:
    held = store.get(actor.session_id)
    if held is None:
        raise not_found("There is no draft to show.")
    return DraftResponse(
        status="draft" if held.draft else "fallback",
        draft=held.draft,
        source_text=held.text,
        fallback=None if held.draft else controls.fallback("ai_unavailable"),
        trace_id=held.trace_id,
    )


def accept(db: Session, actor: Actor, body: DraftAccept) -> None:
    """W23: save only the fields the author submitted, with their visibility, then delete
    the raw text. The author's submission is validated like any profile edit; the model's
    draft itself is never written (CR-009)."""
    held = store.get(actor.session_id)
    if held is None:
        raise not_found("There is no draft to save. Your profile was not changed.")
    values = {
        ProfileField.interests.value: body.interests,
        ProfileField.challenges.value: body.challenges,
        ProfileField.looking_for.value: body.looking_for,
        ProfileField.industry.value: body.industry,
        ProfileField.summary.value: body.summary,
    }
    values = {k: v for k, v in values.items() if k in body.model_fields_set}
    allowed = {ProfileField(k) for k in values}
    visibility = {k: v for k, v in body.visibility.items() if k in allowed}
    people.write_fields(db, actor.id, values, visibility)
    people.load_profile(db, actor.id).profile.updated_at = policy.now()
    controls.set_review_outcome(db, held.trace_id, "accepted")
    store.pop(actor.session_id)  # raw text deleted (MN-015)


def discard(db: Session, actor: Actor) -> None:
    held = store.pop(actor.session_id)
    if held is not None:
        controls.set_review_outcome(db, held.trace_id, "discarded")
