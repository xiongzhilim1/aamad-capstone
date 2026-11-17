"""AI match suggestions: W06 input assembly, W07 the model call, W08 the output check.

`suggest(db, actor, trace_id)` is the only entry point (SAD §4 Runtime Integration Layer).
It reads live data, calls the crew once, and writes nothing except the trace: the model has
no write path to any record (MN-003, CR-009).
"""

import json
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai import controls
from app.ai.guardrails import (
    CircleContext,
    PersonContext,
    SuggestionContext,
    check_suggestions,
    mentions_faith,
)
from app.ai.schemas import Checked, Dropped, SuggestionOut, SuggestionResult
from app.api.deps import Actor
from app.api.schemas.common import AiFallback
from app.api.schemas.discovery import SuggestionItem, SuggestionsResponse
from app.crews import runtime
from app.db.models import Circle
from app.domain.vocab import MATCHING_FIELDS
from app.services import discovery, people, policy
from app.services.people import ProfileData

CREW = "suggestion"
TASK_ID = "suggest_v1"
MAX_PEOPLE = 50  # MC-002, CR-001
MAX_CIRCLES = 20
FAITH = "faith_context"


def _viewer_fields(pd: ProfileData) -> dict[str, Any]:
    """The viewer's own MD-021 fields. Faith only with their matching opt-in (MN-004)."""
    out: dict[str, Any] = {"stage": pd.profile.stage}
    for f in MATCHING_FIELDS:
        value = pd.get(f.value)
        if value in (None, "", []):
            continue
        if f.value == FAITH and not pd.profile.faith_matching_opt_in:
            continue
        out[f.value] = value
    return out


def _person_context(pd: ProfileData, viewer_faith: bool) -> PersonContext:
    """CR-002 field allowlist with the CR-015 citable / rank-only split.

    Only MD-021 fields are read: names, contact details, consent and block state are never
    looked at here, so they cannot reach the prompt. Faith needs both opt-ins.
    """
    faith_allowed = viewer_faith and pd.profile.faith_matching_opt_in
    citable: dict[str, Any] = {"stage": pd.profile.stage}
    rank_only: dict[str, Any] = {}
    for f in MATCHING_FIELDS:
        value = pd.get(f.value)
        if value in (None, "", []):
            continue
        if f.value == FAITH and not faith_allowed:
            continue
        if f.value == "summary" and not faith_allowed and mentions_faith(str(value)):
            continue  # a bio that states a faith is held back unless both opted in
        target = citable if pd.visibility_of(f.value) == "public" else rank_only
        target[f.value] = value
    return PersonContext(citable, rank_only, faith_allowed and FAITH in citable)


def _circle_context(circle: Circle, viewer_faith: bool) -> CircleContext:
    fields: dict[str, Any] = {"purpose": circle.purpose, "tags": circle.tags}
    if circle.area:
        fields["area"] = circle.area
    if circle.meeting_mode:
        fields["meeting_mode"] = circle.meeting_mode
    faith_allowed = viewer_faith and circle.faith_tagged
    if faith_allowed and circle.faith_context_label:
        fields[FAITH] = circle.faith_context_label
    return CircleContext(fields, faith_allowed)


def build_context(
    db: Session, actor: Actor
) -> tuple[SuggestionContext, dict[str, UUID], dict[str, UUID]]:
    """W06: the candidate set, chosen by code and evaluated live (CR-001).

    People: opted in to the directory, not the viewer, not blocked either way, not already
    connected, capped at 50. Circles: not already joined, capped at 20. Faith-tagged circles
    are offered only when the viewer opted faith into matching, and community-tagged circles
    are never offered. Prompt ids are short and
    opaque (`p01`, `c01`), so no database id or name reaches the model.
    """
    viewer = people.load_profile(db, actor.id)
    viewer_faith = viewer.profile.faith_matching_opt_in and bool(viewer.get(FAITH))
    eligible = policy.discoverable_ids(db, actor.id) - set(policy.connected_ids(db, actor.id))
    profiles = people.load_profiles(db, eligible)
    ordered = sorted(profiles.values(), key=lambda p: str(p.user.id))[:MAX_PEOPLE]
    person_ids = {f"p{i:02d}": pd.user.id for i, pd in enumerate(ordered, 1)}
    by_user = {pd.user.id: pd for pd in ordered}
    circles = [
        c
        for c in discovery.all_circles(db)
        if policy.membership_status(db, c.id, actor.id) == "none"
        and (viewer_faith or not c.faith_tagged)
        and not c.community_tagged  # browse-only: origin or background never reaches the model
    ][:MAX_CIRCLES]
    circle_ids = {f"c{i:02d}": c.id for i, c in enumerate(circles, 1)}
    by_circle = {c.id: c for c in circles}
    ctx = SuggestionContext(
        viewer_fields=_viewer_fields(viewer),
        people={k: _person_context(by_user[u], viewer_faith) for k, u in person_ids.items()},
        circles={k: _circle_context(by_circle[c], viewer_faith) for k, c in circle_ids.items()},
    )
    return ctx, person_ids, circle_ids


def render_payload(ctx: SuggestionContext) -> str:
    """The data block of the prompt. Braces are replaced because CrewAI treats `{name}` in
    task text as a template variable; the content is unchanged for the model."""
    data = {
        "viewer": ctx.viewer_fields,
        "people": [
            {"id": k, "citable": p.citable, **({"rank_only": p.rank_only} if p.rank_only else {})}
            for k, p in ctx.people.items()
        ],
        "circles": [{"id": k, **c.fields} for k, c in ctx.circles.items()],
    }
    text = json.dumps(data, ensure_ascii=False, indent=1)
    return text.replace("{", "(").replace("}", ")")


def _fallback(db: Session, actor: Actor, trace_id: str, fb: AiFallback) -> SuggestionsResponse:
    """MC-005: filter discovery still answers, so the page is never empty."""
    return SuggestionsResponse(
        status="fallback",
        fallback=fb,
        filter_results=discovery.discover(db, actor),
        trace_id=trace_id,
    )


def suggest(db: Session, actor: Actor, trace_id: str) -> SuggestionsResponse:
    blocked = controls.preflight(db, actor.id, CREW)
    if blocked is not None:
        if blocked.code != "rate_limited":
            controls.write_trace(
                trace_id=trace_id, crew=CREW, user_id=actor.id, run=None, outcome="fallback",
                fallback_code=blocked.code, task_id=TASK_ID,
            )  # fmt: skip
        return _fallback(db, actor, trace_id, blocked)
    try:
        ctx, person_ids, circle_ids = build_context(db, actor)
    except Exception:  # noqa: BLE001 - CR-001 fails closed: no model call on any error
        controls.log.exception("candidate assembly failed trace_id=%s", trace_id)
        return _fallback(db, actor, trace_id, controls.fallback("ai_unavailable"))
    input_ids = [*ctx.people, *ctx.circles]
    if not input_ids:
        return _fallback(db, actor, trace_id, controls.fallback("no_candidates"))

    def guard(result: SuggestionResult) -> Checked[list[SuggestionOut]]:
        return check_suggestions(result, ctx)

    run = runtime.run_crew(TASK_ID, {"payload": render_payload(ctx)}, SuggestionResult, guard)
    controls.breaker.record(run.failure is None)
    if run.failure is not None:
        code = controls.failure_code(run)
        controls.write_trace(
            trace_id=trace_id, crew=CREW, user_id=actor.id, run=run, outcome="fallback",
            fallback_code=code, input_ids=input_ids,
        )  # fmt: skip
        return _fallback(db, actor, trace_id, controls.fallback(code))

    checked: Checked[list[SuggestionOut]] = run.guarded
    dropped = list(checked.dropped)
    # Display-time re-check (CR-006): someone may have opted out, blocked or been connected
    # while the call was running, so eligibility is evaluated again on fresh data.
    db.expire_all()
    still_people = policy.discoverable_ids(db, actor.id) - set(policy.connected_ids(db, actor.id))
    live_circles = {c.id: c for c in discovery.all_circles(db)}
    items: list[SuggestionItem] = []
    kept_ids: list[str] = []
    cards = {c.id: c for c in people.person_cards(db, actor.id, still_people)}
    for s in checked.value:
        if s.kind == "person":
            user_id = person_ids[s.candidate_id]
            if user_id not in still_people or user_id not in cards:
                dropped.append(Dropped(s.candidate_id, "no_longer_eligible"))
                continue
            items.append(
                SuggestionItem(
                    kind="person",
                    reason=s.reason,
                    cited_fields=s.cited_fields,
                    person=cards[user_id],
                )
            )
        else:
            circle = live_circles.get(circle_ids[s.candidate_id])
            if circle is None or policy.membership_status(db, circle.id, actor.id) != "none":
                dropped.append(Dropped(s.candidate_id, "no_longer_eligible"))
                continue
            card = discovery.circle_cards(db, actor, [circle])[0]
            items.append(
                SuggestionItem(
                    kind="circle", reason=s.reason, cited_fields=s.cited_fields, circle=card
                )
            )
        kept_ids.append(s.candidate_id)
    outcome = "ok" if items else "fallback"
    controls.write_trace(
        trace_id=trace_id, crew=CREW, user_id=actor.id, run=run, outcome=outcome,
        fallback_code=None if items else "ai_unavailable", input_ids=input_ids,
        output_ids=kept_ids, dropped=dropped,
    )  # fmt: skip
    if not items:  # every item was dropped: show the fallback, not an empty AI list
        return _fallback(db, actor, trace_id, controls.fallback("ai_unavailable"))
    return SuggestionsResponse(status="ok", items=items, trace_id=trace_id)
