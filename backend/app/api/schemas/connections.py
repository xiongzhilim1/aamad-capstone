"""Requests, connections, contact sharing, blocks, reports, follow-ups (US-007-010, US-021)."""

from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints

from app.api.schemas.common import ApiModel, PersonCard, PersonRef
from app.api.schemas.profile import ContactDetails


class RequestCreate(ApiModel):
    recipient_id: UUID


class ConnectionRequest(ApiModel):
    """A pending request. Contains no contact fields (MN-002)."""

    id: UUID
    direction: Literal["incoming", "outgoing"]
    person: PersonCard
    created_at: datetime


class RequestInbox(ApiModel):
    """Pending requests only. A declined request stays in `outgoing` for its sender,
    so a decline is never revealed (OQ-06 default)."""

    incoming: list[ConnectionRequest]
    outgoing: list[ConnectionRequest]


class ContactSharing(ApiModel):
    mine: bool
    theirs: bool


class FollowUp(ApiModel):
    """A catch-up self-report. `met` null means no report; false means "we did not meet"."""

    number: Literal[1, 2]
    met: bool | None = None
    period_start: date | None = None
    period_end: date | None = None
    usefulness: int | None = Field(default=None, ge=1, le=5)
    reported_by_me: bool = False


class FollowUpReport(ApiModel):
    met: bool
    period_start: date | None = None
    period_end: date | None = None
    usefulness: int | None = Field(default=None, ge=1, le=5)


class Connection(ApiModel):
    id: UUID
    person: PersonCard
    connected_at: datetime
    contact_sharing: ContactSharing
    their_contact: ContactDetails | None = Field(
        default=None, description="Present only while both sides share (AC-004)."
    )
    follow_ups: list[FollowUp]


class ContactShareUpdate(ApiModel):
    share: bool


class BlockCreate(ApiModel):
    user_id: UUID


class Block(ApiModel):
    person: PersonRef
    created_at: datetime


class ReportCreate(ApiModel):
    subject_id: UUID
    reason: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]


class ReportReceipt(ApiModel):
    id: UUID
    created_at: datetime
