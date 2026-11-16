"""Deterministic output checks: W08 for suggestions, W22 for profile drafts.

Pure functions over crafted inputs, so they are unit-tested without a model (SAD §9).
Every check fails closed per item: an item that fails is dropped, never repaired (CR-006,
CR-007, CR-015).
"""

import re
from dataclasses import dataclass, field
from typing import Any

from app.ai.schemas import Checked, Dropped, ProfileDraftOut, SuggestionOut, SuggestionResult
from app.api.schemas.profile import ProfileDraft
from app.domain import vocab

MAX_ITEMS = 10
CIRCLE_FIELDS = ("purpose", "tags", "area", "meeting_mode", "faith_context")

# Sensitive-attribute terms (CR-007, MN-004, MN-014). Stems match as word prefixes.
FAITH_TERMS = (
    "faith", "christ", "church", "god", "jesus", "pray", "religio", "spiritual", "bible",
    "gospel", "ministry", "pastor", "muslim", "islam", "mosque", "buddh", "hindu", "jewish",
    "catholic", "worship", "believer", "scripture", "sermon", "congregation", "temple",
)  # fmt: skip
HEALTH_TERMS = (
    "health condition", "illness", "disease", "diagnos", "cancer", "depress", "anxiety",
    "therapy", "therapist", "medication", "disabil", "surgery", "hospital", "mental health",
    "burnout", "adhd", "autis", "chronic", "pregnan", "sick",
)  # fmt: skip
FAMILY_TERMS = (
    "wife", "husband", "spouse", "married", "marriage", "divorc", "my kids", "my children",
    "my son", "my daughter", "my mother", "my father", "my parents", "single parent",
    "girlfriend", "boyfriend", "my partner", "newborn", "my baby", "widow",
)  # fmt: skip


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _has_term(text: str, terms: tuple[str, ...]) -> bool:
    low = _norm(text)
    return any(re.search(rf"\b{re.escape(t)}", low) for t in terms)


def mentions_faith(text: str) -> bool:
    return _has_term(text, FAITH_TERMS)


def mentions_sensitive(text: str) -> bool:
    return _has_term(text, FAITH_TERMS + HEALTH_TERMS + FAMILY_TERMS)


def word_count(text: str) -> int:
    return len(text.split())


# --- W08: suggestions ------------------------------------------------------------------


@dataclass
class PersonContext:
    """What the prompt held for one candidate. `citable` is what a reason may rely on."""

    citable: dict[str, Any]
    rank_only: dict[str, Any] = field(default_factory=dict)
    faith_allowed: bool = False


@dataclass
class CircleContext:
    fields: dict[str, Any]
    faith_allowed: bool = False


@dataclass
class SuggestionContext:
    """The exact input set of one request (W06). Ids are the short opaque prompt ids."""

    viewer_fields: dict[str, Any]
    people: dict[str, PersonContext]
    circles: dict[str, CircleContext]


def _phrases(value: Any) -> list[str]:
    """Strings that would reveal a field value if they appeared in a reason."""
    out: list[str] = []
    for v in value if isinstance(value, list) else [value]:
        if not isinstance(v, str) or not v:
            continue
        out.append(v.lower())
        out.append(v.replace("_", " ").lower())
        out.append(vocab.label(v).lower())
    return out


def _leaks(reason: str, rank_only: dict[str, Any]) -> bool:
    """CR-015: exact leak of a matching-only value. Tag ids, tag labels, and any run of three
    consecutive words from matching-only free text. Paraphrase is eval-gated (EC-007)."""
    low = _norm(reason)
    for name, value in rank_only.items():
        if name in ("summary", "faith_context") and isinstance(value, str):
            words = _norm(value).split()
            runs = [" ".join(words[i : i + 3]) for i in range(max(0, len(words) - 2))]
            if any(run in low for run in runs) or (0 < len(words) < 3 and _norm(value) in low):
                return True
            continue
        if any(p in low for p in _phrases(value)):
            return True
    return False


def _present(value: Any) -> bool:
    return value not in (None, "", [])


def _person_problem(item: SuggestionOut, ctx: SuggestionContext) -> str | None:
    person = ctx.people[item.candidate_id]
    for name in item.cited_fields:
        if name not in vocab.CITABLE_FIELD_NAMES:
            return "unknown_field"
        if not _present(person.citable.get(name)):
            return "field_not_citable"  # absent, or matching-only on the candidate
        if not _present(ctx.viewer_fields.get(name)):
            return "field_not_shared"
    if _leaks(item.reason, person.rank_only):
        return "rank_only_leak"
    if mentions_faith(item.reason) and not person.faith_allowed:
        return "faith_without_opt_in"
    if "faith_context" in item.cited_fields and not person.faith_allowed:
        return "faith_without_opt_in"
    return None


def _circle_problem(item: SuggestionOut, ctx: SuggestionContext) -> str | None:
    circle = ctx.circles[item.candidate_id]
    for name in item.cited_fields:
        if name not in CIRCLE_FIELDS or not _present(circle.fields.get(name)):
            return "field_not_citable"
    if mentions_faith(item.reason) and not circle.faith_allowed:
        return "faith_without_opt_in"
    return None


def check_suggestions(
    result: SuggestionResult, ctx: SuggestionContext
) -> Checked[list[SuggestionOut]]:
    """W08 (CR-006, CR-007, CR-015, AC-007, AC-008). Order is kept; at most 10 survive."""
    kept: list[SuggestionOut] = []
    dropped: list[Dropped] = []
    seen: set[str] = set()
    for item in result.items:
        pool: dict[str, Any] = ctx.people if item.kind == "person" else ctx.circles
        problem: str | None
        if item.candidate_id not in pool:
            problem = "id_not_in_input_set"
        elif item.candidate_id in seen:
            problem = "duplicate"
        elif not item.cited_fields:
            problem = "no_cited_field"
        elif not item.reason.strip() or word_count(item.reason) > vocab.REASON_MAX_WORDS:
            problem = "reason_length"
        elif item.kind == "person":
            problem = _person_problem(item, ctx)
        else:
            problem = _circle_problem(item, ctx)
        if problem is None and len(kept) >= MAX_ITEMS:
            problem = "over_limit"
        if problem is not None:
            # Only ids that were in the prompt are logged; an invented id is logged as a marker.
            known = item.candidate_id if item.candidate_id in pool else "unknown"
            dropped.append(Dropped(known, problem))
            continue
        seen.add(item.candidate_id)
        kept.append(item)
    return Checked(kept, dropped)


# --- W22: profile drafts ---------------------------------------------------------------


def _quoted(evidence: str, source: str) -> bool:
    quote = _norm(evidence).strip(" .,;:!?\"'")
    return len(quote) >= 3 and quote in _norm(source)


_FILLER = (
    "this that with from their they them what which who whose about wants want looking look "
    "seeks seek owner founder runs running business entrepreneur person someone while also "
    "needs need help would like hopes hope aims plans works"
)


def _stems(text: str) -> set[str]:
    return {w[:5] for w in re.findall(r"[a-z]{4,}", text.lower())}


def summary_is_grounded(summary: str, source: str) -> bool:
    """A cheap no-invention check: most content words of the summary occur in the source.

    Paraphrase beyond this is measured by the MP-007 eval (EC-004), not here.
    """
    words = _stems(summary) - _stems(_FILLER)
    if not words:
        return True
    return len(words & _stems(source)) / len(words) >= 0.6


def check_draft(out: ProfileDraftOut, source: str) -> Checked[ProfileDraft]:
    """W22 (MN-014, AC-018, EC-004): each tag needs a verbatim quote from the author's text,
    and nothing sensitive (faith, health, family) may come out, even when the text has it."""
    dropped: list[Dropped] = []

    def keep(kind: str, tags: list[Any]) -> list[Any]:
        kept: list[Any] = []
        for t in tags:
            value = t.tag.value
            if not _quoted(t.evidence, source):
                dropped.append(Dropped(f"{kind}:{value}", "not_traceable"))
            elif mentions_sensitive(t.evidence):
                dropped.append(Dropped(f"{kind}:{value}", "sensitive_evidence"))
            elif t.tag not in kept:
                kept.append(t.tag)
        return kept[: vocab.TAGS_MAX]

    industry = keep("industry", [out.industry] if out.industry else [])
    summary: str | None = out.summary.strip()
    if not summary:
        summary = None
    elif len(summary) > vocab.SUMMARY_MAX:
        dropped.append(Dropped("summary", "too_long"))
        summary = None
    elif mentions_sensitive(summary):
        dropped.append(Dropped("summary", "sensitive"))
        summary = None
    elif not summary_is_grounded(summary, source):
        dropped.append(Dropped("summary", "not_traceable"))
        summary = None
    draft = ProfileDraft(
        interests=keep("interests", out.interests),
        challenges=keep("challenges", out.challenges),
        looking_for=keep("looking_for", out.looking_for),
        industry=industry[0] if industry else None,
        summary=summary,
    )
    return Checked(draft, dropped)
