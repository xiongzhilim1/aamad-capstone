"""Events, registration, attendance, reconnection (US-004, US-012-015, US-018-020, US-025)."""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import Field, StringConstraints

from app.api.schemas.common import ApiModel, PersonCard, PersonRef
from app.domain.vocab import (
    AttendanceSource,
    AttendanceStatus,
    Decision,
    EventMode,
    EventState,
)

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
LongText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]
Timezone = Annotated[str, StringConstraints(min_length=1, max_length=64)]


class Venue(ApiModel):
    """Curated by the admin. Null fields render as "Unknown" (MD-014, AC-012).

    Informational only: there is no booking or payment anywhere in this API (MN-009).
    """

    id: UUID
    name: str
    area: str | None = None
    address_hint: str | None = Field(default=None, description="Coarse, e.g. a street or building.")
    capacity: int | None = None
    notes: str | None = None
    synthetic: bool = True


class VenueWrite(ApiModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
    area: ShortText | None = None
    address_hint: ShortText | None = None
    capacity: int | None = Field(default=None, ge=1, le=100000)
    notes: ShortText | None = None


class EventWrite(ApiModel):
    """Create or replace a draft. `starts_at` may be in the past (MD-025)."""

    title: Title
    description: LongText | None = None
    starts_at: datetime = Field(description="Timezone-aware ISO 8601.")
    ends_at: datetime
    timezone: Timezone = "Asia/Hong_Kong"
    mode: EventMode
    venue_id: UUID | None = None
    venue_text: ShortText | None = Field(
        default=None, description="Free text when not in the directory."
    )
    capacity: int | None = Field(default=None, ge=1, le=100000)
    price_amount: Decimal | None = Field(default=None, ge=0, max_digits=8, decimal_places=2)
    price_currency: Currency | None = None
    includes: ShortText | None = Field(default=None, description="What the price includes.")
    circle_id: UUID | None = Field(
        default=None, description="Optional link to one circle (US-019)."
    )


class EventApproval(ApiModel):
    """One admin decision (MP-002, NFR-008)."""

    admin: PersonRef
    decision: Decision
    reason: str | None = None
    decided_at: datetime


class MyEventStatus(ApiModel):
    """The viewer's own facts about an event. Three separate facts, never merged (MD-012)."""

    registered: bool
    attendance: AttendanceStatus
    attendance_source: AttendanceSource | None = None
    reconnect_opted_in: bool
    can_manage: bool = Field(description="Organiser or co-host of this event.")
    is_organiser: bool


class EventCard(ApiModel):
    id: UUID
    title: str
    starts_at: datetime
    ends_at: datetime
    timezone: str
    mode: EventMode
    venue_name: str | None = None
    price_amount: Decimal | None = None
    price_currency: str | None = None
    state: EventState
    added_after_event: bool = Field(description="Created after it took place (MD-025).")
    has_ended: bool
    my: MyEventStatus


class EventDetail(EventCard):
    description: str | None = None
    venue: Venue | None = None
    venue_text: str | None = None
    capacity: int | None = None
    includes: str | None = None
    organiser: PersonRef
    co_hosts: list[PersonRef]
    circle: PersonRef | None = Field(
        default=None,
        description="Linked circle as `{id, display_name}`; grants no access (MN-006).",
    )
    registered_count: int
    approvals: list[EventApproval] | None = Field(
        default=None, description="Decision log. Organiser, co-hosts and admin only."
    )


class AttendanceMark(ApiModel):
    user_id: UUID
    attended: bool


class AttendanceRow(ApiModel):
    user_id: UUID
    display_name: str
    registered: bool
    registered_at: datetime | None = None
    attendance: AttendanceStatus
    source: AttendanceSource | None = None
    updated_at: datetime | None = None


class AttendanceClaim(ApiModel):
    claim_id: UUID
    user_id: UUID
    display_name: str
    claimed_at: datetime


class CheckinCodeState(ApiModel):
    """The code is returned once, by `PUT /events/{id}/checkin-code`; only a hash is stored."""

    active: bool
    valid_until: datetime | None = None


class CheckinCodeIssued(CheckinCodeState):
    code: str = Field(description="Show and copy now; it cannot be read again (CR-017).")


class AttendanceCounts(ApiModel):
    """Separate counts with separate meanings (MD-012, PRD-v0 E06)."""

    registered: int
    confirmed: int
    confirmed_by_organiser: int
    confirmed_by_claim: int
    confirmed_by_code: int
    claims_pending: int


class HostAttendance(ApiModel):
    """Host tools: Attendance (US-015). Organiser and co-hosts only."""

    people: list[AttendanceRow]
    claims: list[AttendanceClaim]
    joined_by_code: list[AttendanceRow]
    counts: AttendanceCounts
    checkin_code: CheckinCodeState


class RegistrationResult(ApiModel):
    event_id: UUID
    registered: bool


class AttendanceResult(ApiModel):
    event_id: UUID
    attendance: AttendanceStatus
    attendance_source: AttendanceSource | None = None


class CheckinRequest(ApiModel):
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=4, max_length=12)]


class ReconnectConsentUpdate(ApiModel):
    opted_in: bool


class ReconnectList(ApiModel):
    """Confirmed and opted-in attendees of one ended event, minus blocks (MD-003, AC-002)."""

    event_id: UUID
    people: list[PersonCard]


class EventDecisionRequest(ApiModel):
    decision: Decision
    reason: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = None
