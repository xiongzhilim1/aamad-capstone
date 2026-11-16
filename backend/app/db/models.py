"""Data model (SAD §4 Data Architecture). Supabase is used as plain Postgres.

Authorization does not live here: see `app/services/policy.py`.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSON, list[str]: JSON, datetime: DateTime(timezone=True)}


def _pk() -> Mapped[uuid.UUID]:
    return mapped_column(primary_key=True, default=uuid.uuid4)


def _fk(target: str, **kw: Any) -> Mapped[uuid.UUID]:
    return mapped_column(ForeignKey(target, ondelete="CASCADE"), **kw)


def _now() -> Mapped[datetime]:
    return mapped_column(server_default=func.now())


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = _pk()
    display_name: Mapped[str] = mapped_column(String(60))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_organiser: Mapped[bool] = mapped_column(Boolean, default=False)
    persona_blurb: Mapped[str] = mapped_column(String(200), default="")
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)  # MN-008
    created_at: Mapped[datetime] = _now()


class Profile(Base):
    __tablename__ = "profiles"
    user_id: Mapped[uuid.UUID] = _fk("users.id", primary_key=True)
    stage: Mapped[str] = mapped_column(String(16))
    faith_matching_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)  # MN-004
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    contact_email: Mapped[str | None] = mapped_column(String(120))
    contact_phone: Mapped[str | None] = mapped_column(String(120))
    contact_other: Mapped[str | None] = mapped_column(String(120))
    updated_at: Mapped[datetime] = _now()
    __table_args__ = (
        CheckConstraint("stage in ('seasoned','new','aspiring')", name="stage_valid"),
    )


class ProfileFieldRow(Base):
    """One optional profile field with its visibility (MD-020)."""

    __tablename__ = "profile_fields"
    user_id: Mapped[uuid.UUID] = _fk("users.id", primary_key=True)
    field: Mapped[str] = mapped_column(String(24), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON)
    visibility: Mapped[str] = mapped_column(String(16), default="public")
    __table_args__ = (
        CheckConstraint("visibility in ('public','matching_only')", name="visibility_valid"),
    )


class DiscoveryConsent(Base):
    """A row is a consent. `event_id` null is the global directory consent (MD-002, MD-003)."""

    __tablename__ = "discovery_consents"
    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = _fk("users.id")
    event_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = _now()
    __table_args__ = (
        Index(
            "uq_consent_global", "user_id", unique=True, postgresql_where=text("event_id is null")
        ),
        Index(
            "uq_consent_event",
            "user_id",
            "event_id",
            unique=True,
            postgresql_where=text("event_id is not null"),
        ),
    )


class ConnectionRequestRow(Base):
    __tablename__ = "connection_requests"
    id: Mapped[uuid.UUID] = _pk()
    sender_id: Mapped[uuid.UUID] = _fk("users.id")
    recipient_id: Mapped[uuid.UUID] = _fk("users.id")
    status: Mapped[str] = mapped_column(String(12), default="pending")
    # A declined request stays visible to its sender as pending unless they withdraw it (OQ-06).
    sender_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = _now()
    responded_at: Mapped[datetime | None] = mapped_column()
    __table_args__ = (
        CheckConstraint("sender_id <> recipient_id", name="not_self"),
        CheckConstraint(
            "status in ('pending','accepted','declined','withdrawn')", name="status_valid"
        ),
        Index(
            "uq_request_open",
            "sender_id",
            "recipient_id",
            unique=True,
            postgresql_where=text("status in ('pending','declined')"),
        ),
    )


class ConnectionRow(Base):
    """An accepted pair, stored once with `user_a < user_b`."""

    __tablename__ = "connections"
    id: Mapped[uuid.UUID] = _pk()
    user_a: Mapped[uuid.UUID] = _fk("users.id")
    user_b: Mapped[uuid.UUID] = _fk("users.id")
    request_id: Mapped[uuid.UUID] = _fk("connection_requests.id")
    created_at: Mapped[datetime] = _now()
    __table_args__ = (
        UniqueConstraint("user_a", "user_b"),
        CheckConstraint("user_a < user_b", name="ordered_pair"),
    )


class ContactShare(Base):
    """A row is one side's grant. Contacts show only when both sides have a row (MD-007)."""

    __tablename__ = "contact_shares"
    connection_id: Mapped[uuid.UUID] = _fk("connections.id", primary_key=True)
    user_id: Mapped[uuid.UUID] = _fk("users.id", primary_key=True)
    created_at: Mapped[datetime] = _now()


class BlockRow(Base):
    __tablename__ = "blocks"
    blocker_id: Mapped[uuid.UUID] = _fk("users.id", primary_key=True)
    blocked_id: Mapped[uuid.UUID] = _fk("users.id", primary_key=True)
    created_at: Mapped[datetime] = _now()


class ReportRow(Base):
    __tablename__ = "reports"
    id: Mapped[uuid.UUID] = _pk()
    reporter_id: Mapped[uuid.UUID] = _fk("users.id")
    subject_id: Mapped[uuid.UUID] = _fk("users.id")
    reason: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = _now()


class Circle(Base):
    __tablename__ = "circles"
    id: Mapped[uuid.UUID] = _pk()
    name: Mapped[str] = mapped_column(String(80))
    purpose: Mapped[str] = mapped_column(String(400))
    tags: Mapped[list[str]] = mapped_column(default=list)
    admission_policy: Mapped[str] = mapped_column(String(12), default="approval")
    member_list_visibility: Mapped[str] = mapped_column(String(12), default="members")
    meeting_mode: Mapped[str | None] = mapped_column(String(12))
    area: Mapped[str | None] = mapped_column(String(24))
    faith_tagged: Mapped[bool] = mapped_column(Boolean, default=False)
    faith_context_label: Mapped[str | None] = mapped_column(String(40))
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = _now()


class CircleMembership(Base):
    __tablename__ = "circle_memberships"
    circle_id: Mapped[uuid.UUID] = _fk("circles.id", primary_key=True)
    user_id: Mapped[uuid.UUID] = _fk("users.id", primary_key=True)
    status: Mapped[str] = mapped_column(String(12))
    created_at: Mapped[datetime] = _now()
    __table_args__ = (CheckConstraint("status in ('member','applicant')", name="status_valid"),)


class CircleFacilitator(Base):
    __tablename__ = "circle_facilitators"
    circle_id: Mapped[uuid.UUID] = _fk("circles.id", primary_key=True)
    user_id: Mapped[uuid.UUID] = _fk("users.id", primary_key=True)


class VenueRow(Base):
    __tablename__ = "venues"
    id: Mapped[uuid.UUID] = _pk()
    name: Mapped[str] = mapped_column(String(120))
    area: Mapped[str | None] = mapped_column(String(200))
    address_hint: Mapped[str | None] = mapped_column(String(200))
    capacity: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(String(200))
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)  # MN-010


class Event(Base):
    __tablename__ = "events"
    id: Mapped[uuid.UUID] = _pk()
    organiser_id: Mapped[uuid.UUID] = _fk("users.id")
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column()
    ends_at: Mapped[datetime] = mapped_column()
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Hong_Kong")
    mode: Mapped[str] = mapped_column(String(12))
    venue_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("venues.id", ondelete="SET NULL"))
    venue_text: Mapped[str | None] = mapped_column(String(200))
    capacity: Mapped[int | None] = mapped_column(Integer)
    price_amount: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    price_currency: Mapped[str | None] = mapped_column(String(3))
    includes: Mapped[str | None] = mapped_column(String(200))
    circle_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("circles.id", ondelete="SET NULL")
    )
    state: Mapped[str] = mapped_column(String(12), default="draft")
    added_after_event: Mapped[bool] = mapped_column(Boolean, default=False)  # MD-025
    synthetic: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = _now()
    __table_args__ = (
        CheckConstraint(
            "state in ('draft','submitted','approved','rejected','cancelled')", name="state_valid"
        ),
        CheckConstraint("ends_at > starts_at", name="ends_after_start"),
    )


class EventHost(Base):
    """Co-hosts. The organiser is `events.organiser_id` (MD-013)."""

    __tablename__ = "event_hosts"
    event_id: Mapped[uuid.UUID] = _fk("events.id", primary_key=True)
    user_id: Mapped[uuid.UUID] = _fk("users.id", primary_key=True)


class EventApprovalRow(Base):
    """The admin decision log (MP-002). An event is published only with an `approve` row."""

    __tablename__ = "event_approvals"
    id: Mapped[uuid.UUID] = _pk()
    event_id: Mapped[uuid.UUID] = _fk("events.id")
    admin_id: Mapped[uuid.UUID] = _fk("users.id")
    decision: Mapped[str] = mapped_column(String(8))
    reason: Mapped[str | None] = mapped_column(String(500))
    decided_at: Mapped[datetime] = _now()


class Registration(Base):
    """Intent to come. Never attendance, never membership (MD-012, MN-007)."""

    __tablename__ = "registrations"
    event_id: Mapped[uuid.UUID] = _fk("events.id", primary_key=True)
    user_id: Mapped[uuid.UUID] = _fk("users.id", primary_key=True)
    created_at: Mapped[datetime] = _now()


class Attendance(Base):
    __tablename__ = "attendance"
    id: Mapped[uuid.UUID] = _pk()
    event_id: Mapped[uuid.UUID] = _fk("events.id")
    user_id: Mapped[uuid.UUID] = _fk("users.id")
    status: Mapped[str] = mapped_column(String(12))
    source: Mapped[str] = mapped_column(String(12))
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = _now()
    __table_args__ = (
        UniqueConstraint("event_id", "user_id"),
        CheckConstraint("status in ('claimed','confirmed','declined')", name="status_valid"),
        CheckConstraint("source in ('organiser','claim','code')", name="source_valid"),
    )


class AttendanceLog(Base):
    """Every attendance change, so corrections are recorded (US-015)."""

    __tablename__ = "attendance_log"
    id: Mapped[uuid.UUID] = _pk()
    event_id: Mapped[uuid.UUID] = _fk("events.id")
    user_id: Mapped[uuid.UUID] = _fk("users.id")
    from_status: Mapped[str] = mapped_column(String(12))
    to_status: Mapped[str] = mapped_column(String(12))
    actor_id: Mapped[uuid.UUID] = _fk("users.id")
    created_at: Mapped[datetime] = _now()


class EventCheckinCode(Base):
    """One code per event, stored as a keyed hash (CR-017)."""

    __tablename__ = "event_checkin_codes"
    event_id: Mapped[uuid.UUID] = _fk("events.id", primary_key=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    valid_until: Mapped[datetime] = mapped_column()
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    rotated_at: Mapped[datetime] = _now()


class CheckinAttempt(Base):
    __tablename__ = "checkin_attempts"
    id: Mapped[uuid.UUID] = _pk()
    user_id: Mapped[uuid.UUID] = _fk("users.id")
    event_id: Mapped[uuid.UUID] = _fk("events.id")
    succeeded: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = _now()


class FollowUpReportRow(Base):
    """One member's self-report for catch-up 1 or 2. No conversation content (MD-015)."""

    __tablename__ = "follow_up_reports"
    connection_id: Mapped[uuid.UUID] = _fk("connections.id", primary_key=True)
    number: Mapped[int] = mapped_column(Integer, primary_key=True)
    reporter_id: Mapped[uuid.UUID] = _fk("users.id", primary_key=True)
    met: Mapped[bool] = mapped_column(Boolean)
    period_start: Mapped[date | None] = mapped_column(Date)
    period_end: Mapped[date | None] = mapped_column(Date)
    usefulness: Mapped[int | None] = mapped_column(Integer)
    updated_at: Mapped[datetime] = _now()
    __table_args__ = (CheckConstraint("number in (1, 2)", name="number_valid"),)


class StaffAccessLog(Base):
    """Every staff view of `matching_only` fields (MD-022, CR-016)."""

    __tablename__ = "staff_access_log"
    id: Mapped[uuid.UUID] = _pk()
    viewer_id: Mapped[uuid.UUID] = _fk("users.id")
    viewer_role: Mapped[str] = mapped_column(String(12))
    subject_id: Mapped[uuid.UUID] = _fk("users.id")
    fields: Mapped[list[str]] = mapped_column(default=list)
    circle_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("circles.id", ondelete="SET NULL")
    )
    viewed_at: Mapped[datetime] = _now()


class ModelTrace(Base):
    """Per-request decision log for model calls: ids and counts only, never content (CR-013)."""

    __tablename__ = "model_traces"
    id: Mapped[uuid.UUID] = _pk()
    trace_id: Mapped[str] = mapped_column(String(32), index=True)
    crew: Mapped[str] = mapped_column(String(24))
    task_id: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(48))
    effort: Mapped[str] = mapped_column(String(8))
    user_id: Mapped[uuid.UUID] = _fk("users.id")
    outcome: Mapped[str] = mapped_column(String(12))
    fallback_code: Mapped[str | None] = mapped_column(String(24))
    input_ids: Mapped[list[str]] = mapped_column(default=list)
    output_ids: Mapped[list[str]] = mapped_column(default=list)
    dropped: Mapped[list[str]] = mapped_column(default=list)
    model_calls: Mapped[int] = mapped_column(Integer, default=0)
    schema_failures: Mapped[int] = mapped_column(Integer, default=0)
    stop_reason: Mapped[str | None] = mapped_column(String(24))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=Decimal("0"))
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    review_outcome: Mapped[str | None] = mapped_column(String(12))
    created_at: Mapped[datetime] = _now()
    __table_args__ = (Index("ix_traces_user_crew_time", "user_id", "crew", "created_at"),)
