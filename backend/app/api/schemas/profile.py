"""Own profile, consent and the AI profile assistant (US-002, US-003, US-023, US-024)."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints

from app.api.schemas.common import AiFallback, ApiModel
from app.domain.vocab import (
    FAITH_CONTEXT_MAX,
    FREE_TEXT_MAX,
    SUMMARY_MAX,
    TAGS_MAX,
    Area,
    Challenge,
    Industry,
    Interest,
    LookingFor,
    MeetingMode,
    ProfileField,
    Stage,
    TimeWindow,
    Visibility,
)

DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
Summary = Annotated[str, StringConstraints(strip_whitespace=True, max_length=SUMMARY_MAX)]
ContactLine = Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)]


class LabelledValue(ApiModel):
    value: str
    label: str


class Vocabulary(ApiModel):
    """The closed tag lists the pickers render. Values are stable; labels may change."""

    stages: list[LabelledValue]
    interests: list[LabelledValue]
    challenges: list[LabelledValue]
    looking_for: list[LabelledValue]
    industries: list[LabelledValue]
    areas: list[LabelledValue]
    meeting_modes: list[LabelledValue]
    time_windows: list[LabelledValue]
    visibility_fields: list[LabelledValue] = Field(
        description="Profile fields that take a Public / Private: matching setting."
    )
    limits: dict[str, int] = Field(
        description="`summary_max`, `free_text_max`, `faith_context_max`, `tags_max`."
    )


class ContactDetails(ApiModel):
    """Shown to a connection only when both sides share (MD-007). Synthetic values only."""

    email: ContactLine | None = None
    phone: ContactLine | None = None
    other: ContactLine | None = Field(
        default=None, description="e.g. a WhatsApp or LinkedIn handle"
    )


class ProfileFields(ApiModel):
    """Editable profile content. Only display name and stage are required (MD-001)."""

    display_name: DisplayName
    stage: Stage
    looking_for: list[LookingFor] = Field(default=[], max_length=TAGS_MAX)
    interests: list[Interest] = Field(default=[], max_length=TAGS_MAX)
    challenges: list[Challenge] = Field(default=[], max_length=TAGS_MAX)
    industry: Industry | None = None
    summary: Summary | None = None
    area: Area | None = None
    meeting_mode: MeetingMode | None = None
    time_windows: list[TimeWindow] = Field(default=[], max_length=3)
    faith_context: (
        Annotated[str, StringConstraints(strip_whitespace=True, max_length=FAITH_CONTEXT_MAX)]
        | None
    ) = Field(default=None, description="Optional free self-description; never inferred (MN-004).")
    faith_matching_opt_in: bool = Field(
        default=False, description="Lets suggestions use faith context. Off by default."
    )
    visibility: dict[ProfileField, Visibility] = Field(
        default={},
        description="Per-field setting. Omitted fields keep their current value; "
        "new fields default to `public`, except `faith_context` (`matching_only`).",
    )
    contact: ContactDetails = ContactDetails()


class ProfileUpdate(ProfileFields):
    """Full replacement of the editable profile. Never changes discovery consent (MN-001)."""

    onboarding_completed: bool | None = Field(
        default=None, description="Set true when the onboarding flow finishes or is skipped."
    )


class OwnProfile(ProfileFields):
    """The signed-in user's own profile, including private fields and consent state."""

    visibility: dict[ProfileField, Visibility]
    directory_listed: bool = Field(description="Global discovery consent (MD-002). Default false.")
    onboarding_completed: bool
    updated_at: datetime


class DirectoryConsentUpdate(ApiModel):
    listed: bool


class DraftRequest(ApiModel):
    text: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=FREE_TEXT_MAX)
    ] = Field(description="The author's own words. Held in the server session only (MN-015).")


class ProfileDraft(ApiModel):
    """What the assistant drafted. Not saved until accepted (MN-013)."""

    interests: list[Interest] = []
    challenges: list[Challenge] = []
    looking_for: list[LookingFor] = []
    industry: Industry | None = None
    summary: Summary | None = None


class DraftResponse(ApiModel):
    """`draft`: review it. `fallback`: the assistant is unavailable, use the manual pickers."""

    status: Literal["draft", "fallback"]
    draft: ProfileDraft | None = None
    source_text: str | None = Field(
        default=None, description="The author's text, echoed so the form can keep it."
    )
    fallback: AiFallback | None = None
    trace_id: str | None = None


class DraftAccept(ProfileDraft):
    """The fields the author chose to keep, after any edits. Only these are saved (AC-017)."""

    interests: list[Interest] = Field(default=[], max_length=TAGS_MAX)
    challenges: list[Challenge] = Field(default=[], max_length=TAGS_MAX)
    looking_for: list[LookingFor] = Field(default=[], max_length=TAGS_MAX)
    visibility: dict[ProfileField, Visibility] = {}


class MatchingFieldsView(ApiModel):
    """A participant's `matching_only` fields as shown to permitted staff (MD-022, CR-016).

    Every successful read writes a staff access-log entry.
    """

    subject_id: UUID
    display_name: str
    fields: dict[ProfileField, list[str] | str | None] = Field(
        description="Only fields the subject marked `matching_only`."
    )
    access_log_id: UUID
