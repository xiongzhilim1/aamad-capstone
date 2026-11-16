"""Model-facing output schemas (`output_pydantic`) and the checked results passed to routes."""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel

from app.domain.vocab import Challenge, Industry, Interest, LookingFor


class SuggestionOut(BaseModel):
    candidate_id: str
    kind: Literal["person", "circle"]
    reason: str
    cited_fields: list[str]


class SuggestionResult(BaseModel):
    """SAD §2: `SuggestionResult { items: [{candidate_id, kind, reason, cited_fields}] }`."""

    items: list[SuggestionOut]


class InterestTag(BaseModel):
    tag: Interest
    evidence: str


class ChallengeTag(BaseModel):
    tag: Challenge
    evidence: str


class LookingForTag(BaseModel):
    tag: LookingFor
    evidence: str


class IndustryTag(BaseModel):
    tag: Industry
    evidence: str


class ProfileDraftOut(BaseModel):
    """SAD §2 `ProfileDraft`, plus an evidence quote per tag so W22 can check traceability."""

    interests: list[InterestTag]
    challenges: list[ChallengeTag]
    looking_for: list[LookingForTag]
    industry: IndustryTag | None = None
    summary: str


@dataclass
class Dropped:
    item: str
    reason: str


@dataclass
class Checked[T]:
    """Guardrail output: what survived, and what was dropped and why (ids and codes only)."""

    value: T
    dropped: list[Dropped] = field(default_factory=list)
