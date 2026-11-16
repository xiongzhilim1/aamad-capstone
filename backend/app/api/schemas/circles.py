"""Circles (US-011, US-016, US-017)."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import Field, StringConstraints

from app.api.schemas.common import ApiModel, CircleCard, PersonRef
from app.domain.vocab import (
    AdmissionPolicy,
    Area,
    Challenge,
    Interest,
    MeetingMode,
    MemberListVisibility,
    MembershipStatus,
    Stage,
)

CircleName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
CirclePurpose = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=400)
]
FaithLabel = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]


class LinkedEvent(ApiModel):
    id: UUID
    title: str
    starts_at: datetime


class CircleDetail(CircleCard):
    facilitators: list[PersonRef]
    member_list_visibility: MemberListVisibility
    members: list[PersonRef] | None = Field(
        default=None, description="Null when the viewer may not see the member list (MD-009)."
    )
    linked_events: list[LinkedEvent] = Field(
        default=[], description="Approved events linked to this circle (US-019)."
    )
    pending_applications: int | None = Field(
        default=None, description="Facilitators and the admin only."
    )


class CircleCreate(ApiModel):
    """Admin only (OQ-04 default): the admin creates a circle and names its facilitator."""

    name: CircleName
    purpose: CirclePurpose
    facilitator_id: UUID
    tags: list[Interest | Challenge] = Field(default=[], max_length=6)
    admission_policy: AdmissionPolicy = AdmissionPolicy.approval
    member_list_visibility: MemberListVisibility = MemberListVisibility.members
    meeting_mode: MeetingMode | None = None
    area: Area | None = None
    faith_tagged: bool = False
    faith_context_label: FaithLabel | None = None


class CircleUpdate(ApiModel):
    """Facilitator or admin. Omitted fields are unchanged."""

    name: CircleName | None = None
    purpose: CirclePurpose | None = None
    tags: list[Interest | Challenge] | None = Field(default=None, max_length=6)
    admission_policy: AdmissionPolicy | None = None
    member_list_visibility: MemberListVisibility | None = None
    meeting_mode: MeetingMode | None = None
    area: Area | None = None
    faith_tagged: bool | None = None
    faith_context_label: FaithLabel | None = None


class MembershipResult(ApiModel):
    circle_id: UUID
    membership: MembershipStatus


class Applicant(ApiModel):
    user_id: UUID
    display_name: str
    stage: Stage
    applied_at: datetime
