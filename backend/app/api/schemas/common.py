"""Shared response shapes: error envelope, people and circle cards (SAD §4)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.vocab import (
    AdmissionPolicy,
    Area,
    Challenge,
    Industry,
    Interest,
    LookingFor,
    MeetingMode,
    MembershipStatus,
    Stage,
    TimeWindow,
)


class ApiModel(BaseModel):
    """Base for every request and response body: unknown keys are rejected (CR-011)."""

    model_config = ConfigDict(extra="forbid")


class FieldError(ApiModel):
    field: str = Field(description="Dotted path of the failing input field.")
    message: str


class ErrorBody(ApiModel):
    code: str = Field(description="Stable machine code, e.g. `not_found`, `rate_limited`.")
    message: str = Field(description="Human-readable; safe to show to the user.")
    fallback: Literal["filters", "manual"] | None = Field(
        default=None, description="What the UI should offer instead, when a fallback exists."
    )
    trace_id: str
    fields: list[FieldError] | None = Field(
        default=None, description="Present on `validation_error` only."
    )
    retry_at: datetime | None = Field(default=None, description="Present on `rate_limited` only.")


class ErrorEnvelope(ApiModel):
    """Every non-2xx response uses this envelope (SAD §4)."""

    error: ErrorBody


class Relationship(ApiModel):
    """How the viewer relates to a person. Never reveals a decline or a block (US-008, US-010)."""

    status: Literal["none", "request_sent", "request_received", "connected"]
    request_id: UUID | None = None
    connection_id: UUID | None = None


class PersonCard(ApiModel):
    """A person as another participant may see them: public fields only (MD-020, NFR-002).

    Fields the owner marked `matching_only` are null or empty here, and contact details are
    never part of this shape.
    """

    id: UUID
    display_name: str
    stage: Stage
    summary: str | None = None
    looking_for: list[LookingFor] = []
    interests: list[Interest] = []
    challenges: list[Challenge] = []
    industry: Industry | None = None
    area: Area | None = None
    meeting_mode: MeetingMode | None = None
    time_windows: list[TimeWindow] = []
    faith_context: str | None = None
    relationship: Relationship


class PersonRef(ApiModel):
    id: UUID
    display_name: str


class CircleCard(ApiModel):
    id: UUID
    name: str
    purpose: str
    tags: list[Interest | Challenge] = Field(
        default=[], description="Topics the circle covers, from the interest and challenge lists."
    )
    faith_tagged: bool = False
    faith_context_label: str | None = Field(
        default=None, description="Shown only on faith-tagged circles, e.g. `Christian`."
    )
    community_tagged: bool = Field(
        default=False,
        description="A circle for people who share a background, such as a country of origin. "
        "Found by browsing only: never part of AI suggestions, and joining writes nothing "
        "to the member's profile.",
    )
    community_label: str | None = Field(
        default=None, description="Shown only on community-tagged circles, e.g. `Filipino`."
    )
    admission_policy: AdmissionPolicy
    meeting_mode: MeetingMode | None = None
    area: Area | None = None
    member_count: int | None = Field(
        default=None, description="Null when the member list is not visible to the viewer."
    )
    my_membership: MembershipStatus
    i_am_facilitator: bool = False


class DiscoverResults(ApiModel):
    people: list[PersonCard]
    circles: list[CircleCard]


class AiFallback(ApiModel):
    """Why an AI action degraded, and what still works (MC-005, MC-006, AC-009)."""

    code: Literal[
        "ai_unavailable", "ai_timeout", "ai_budget_exhausted", "rate_limited", "no_candidates"
    ]
    message: str
    retry_at: datetime | None = None
