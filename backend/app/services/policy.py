"""The policy module: every visibility, consent and role rule lives here (SAD §4, §8).

Routes and services ask these functions; they never re-derive a rule. Everything is evaluated
live against the database at request time (no cached eligibility), because consent, blocks
and attendance can change at any moment (SAD Reference Architecture).
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, exists, or_, select
from sqlalchemy.orm import Session, aliased

from app.api.deps import Actor
from app.api.errors import ApiError, forbidden, not_found
from app.db.models import (
    Attendance,
    BlockRow,
    Circle,
    CircleFacilitator,
    CircleMembership,
    ConnectionRow,
    DiscoveryConsent,
    Event,
    EventHost,
)


def now() -> datetime:
    return datetime.now(UTC)


# --- blocks (MD-008) -------------------------------------------------------------------


def blocked_ids(db: Session, user_id: UUID) -> set[UUID]:
    """Everyone blocked by, or blocking, this user. Blocks hide both ways."""
    rows = db.execute(
        select(BlockRow.blocker_id, BlockRow.blocked_id).where(
            or_(BlockRow.blocker_id == user_id, BlockRow.blocked_id == user_id)
        )
    ).all()
    return {b if a == user_id else a for a, b in rows}


def is_blocked_pair(db: Session, a: UUID, b: UUID) -> bool:
    return b in blocked_ids(db, a)


# --- discovery consent (MD-002, MD-003) ------------------------------------------------


def listed_ids(db: Session) -> set[UUID]:
    """People with the global directory consent. Default is not listed (MN-001)."""
    return set(
        db.scalars(select(DiscoveryConsent.user_id).where(DiscoveryConsent.event_id.is_(None)))
    )


def is_listed(db: Session, user_id: UUID) -> bool:
    return bool(
        db.scalar(
            select(
                exists().where(
                    DiscoveryConsent.user_id == user_id, DiscoveryConsent.event_id.is_(None)
                )
            )
        )
    )


def has_confirmed_attendance(db: Session, event_id: UUID, user_id: UUID) -> bool:
    return bool(
        db.scalar(
            select(
                exists().where(
                    Attendance.event_id == event_id,
                    Attendance.user_id == user_id,
                    Attendance.status == "confirmed",
                )
            )
        )
    )


def reconnect_member_ids(db: Session, event_id: UUID) -> set[UUID]:
    """Confirmed attendees who opted in for this event. A registration alone never qualifies."""
    return set(
        db.scalars(
            select(DiscoveryConsent.user_id)
            .join(
                Attendance,
                and_(
                    Attendance.event_id == DiscoveryConsent.event_id,
                    Attendance.user_id == DiscoveryConsent.user_id,
                ),
            )
            .where(DiscoveryConsent.event_id == event_id, Attendance.status == "confirmed")
        )
    )


def reconnect_peer_ids(db: Session, viewer_id: UUID) -> set[UUID]:
    """People who share at least one reconnection list with the viewer (ended, approved events)."""
    mine, theirs = aliased(DiscoveryConsent), aliased(DiscoveryConsent)
    my_att, their_att = aliased(Attendance), aliased(Attendance)
    stmt = (
        select(theirs.user_id)
        .join(mine, mine.event_id == theirs.event_id)
        .join(Event, Event.id == theirs.event_id)
        .join(my_att, and_(my_att.event_id == mine.event_id, my_att.user_id == mine.user_id))
        .join(
            their_att,
            and_(their_att.event_id == theirs.event_id, their_att.user_id == theirs.user_id),
        )
        .where(
            mine.user_id == viewer_id,
            theirs.user_id != viewer_id,
            my_att.status == "confirmed",
            their_att.status == "confirmed",
            Event.state == "approved",
            Event.ends_at <= now(),
        )
    )
    return set(db.scalars(stmt))


def discoverable_ids(db: Session, viewer_id: UUID) -> set[UUID]:
    """Who may appear to the viewer in the directory, filters and suggestions (AC-001, AC-005)."""
    return listed_ids(db) - {viewer_id} - blocked_ids(db, viewer_id)


def visible_people_ids(db: Session, viewer_id: UUID) -> set[UUID]:
    """Everyone the viewer can currently see on some surface, so may send a request to (US-007)."""
    reachable = listed_ids(db) | reconnect_peer_ids(db, viewer_id)
    return reachable - {viewer_id} - blocked_ids(db, viewer_id)


# --- connections: pair privacy (MN-006) ------------------------------------------------


def connection_for_member(db: Session, connection_id: UUID, actor_id: UUID) -> ConnectionRow:
    """Private pair data: anyone outside the pair gets not-found, whatever their role (AC-010)."""
    row = db.get(ConnectionRow, connection_id)
    if row is None or actor_id not in (row.user_a, row.user_b):
        raise not_found()
    return row


def connected_ids(db: Session, user_id: UUID) -> dict[UUID, UUID]:
    """other user id -> connection id."""
    rows = db.execute(
        select(ConnectionRow.id, ConnectionRow.user_a, ConnectionRow.user_b).where(
            or_(ConnectionRow.user_a == user_id, ConnectionRow.user_b == user_id)
        )
    ).all()
    return {(b if a == user_id else a): cid for cid, a, b in rows}


# --- events: publication gate and hosts (MD-011, MD-013) -------------------------------

PUBLIC_EVENT_STATES = ("approved", "cancelled")


def co_host_ids(db: Session, event_id: UUID) -> set[UUID]:
    return set(db.scalars(select(EventHost.user_id).where(EventHost.event_id == event_id)))


def can_manage_event(db: Session, event: Event, actor_id: UUID) -> bool:
    """Organiser or assigned co-host of this event only. Admin approves but does not host."""
    return event.organiser_id == actor_id or actor_id in co_host_ids(db, event.id)


def visible_event(db: Session, event_id: UUID, actor: Actor) -> Event:
    """The publication gate (AC-006): an unapproved event does not exist for anyone but its
    organiser, its co-hosts and the admin, on every endpoint that takes an event id."""
    event = db.get(Event, event_id)
    if event is None:
        raise not_found()
    if event.state in PUBLIC_EVENT_STATES or actor.is_admin:
        return event
    if can_manage_event(db, event, actor.id):
        return event
    raise not_found()


def published_event(db: Session, event_id: UUID, actor: Actor) -> Event:
    """For participant actions (register, claim, code, reconnect): approved events only (MN-017).

    Unpublished events stay not-found here even for their organiser, so no participant-side
    path can act on an event that has no approval record.
    """
    event = db.get(Event, event_id)
    if event is None or event.state != "approved":
        if event is not None and event.state == "cancelled":
            raise ApiError(409, "event_cancelled", "This event was cancelled.")
        raise not_found()
    return event


def managed_event(db: Session, event_id: UUID, actor: Actor) -> Event:
    """Host tools: organiser or co-host. Others get 404 when unpublished, else 403."""
    event = visible_event(db, event_id, actor)
    if not can_manage_event(db, event, actor.id):
        raise forbidden("Only the event's hosts can do that.")
    return event


def organised_event(db: Session, event_id: UUID, actor: Actor) -> Event:
    event = visible_event(db, event_id, actor)
    if event.organiser_id != actor.id:
        raise forbidden("Only the event's organiser can do that.")
    return event


def has_started(event: Event) -> bool:
    return event.starts_at <= now()


def has_ended(event: Event) -> bool:
    return event.ends_at <= now()


# --- circles (MD-009, MD-022) ----------------------------------------------------------


def facilitator_ids(db: Session, circle_id: UUID) -> set[UUID]:
    return set(
        db.scalars(
            select(CircleFacilitator.user_id).where(CircleFacilitator.circle_id == circle_id)
        )
    )


def facilitated_circle_ids(db: Session, user_id: UUID) -> set[UUID]:
    return set(
        db.scalars(select(CircleFacilitator.circle_id).where(CircleFacilitator.user_id == user_id))
    )


def membership_status(db: Session, circle_id: UUID, user_id: UUID) -> str:
    row = db.get(CircleMembership, (circle_id, user_id))
    return row.status if row else "none"


def can_manage_circle(db: Session, circle_id: UUID, actor: Actor) -> bool:
    return actor.is_admin or actor.id in facilitator_ids(db, circle_id)


def managed_circle(db: Session, circle_id: UUID, actor: Actor) -> Circle:
    circle = db.get(Circle, circle_id)
    if circle is None:
        raise not_found()
    if not can_manage_circle(db, circle_id, actor):
        raise forbidden("Only this circle's facilitator or the admin can do that.")
    return circle


def can_view_member_list(db: Session, circle: Circle, actor: Actor) -> bool:
    if can_manage_circle(db, circle.id, actor):
        return True
    if circle.member_list_visibility == "everyone":
        return True
    if circle.member_list_visibility == "members":
        return membership_status(db, circle.id, actor.id) == "member"
    return False


def staff_scope(db: Session, actor: Actor, subject_id: UUID, circle_id: UUID | None) -> str:
    """Who may read `matching_only` fields (MD-022, CR-016). Returns the role used, or raises.

    * admin: anyone.
    * facilitator: only members of, and pending applicants to, a circle they facilitate.
    * organisers, co-hosts and other participants: never.
    Fails closed: any doubt is a refusal, and the caller must write the access log before
    returning the fields.
    """
    if circle_id is None:
        if actor.is_admin:
            return "admin"
        raise forbidden("Only the admin can do that.")
    if db.get(Circle, circle_id) is None:
        raise not_found()
    if actor.id not in facilitator_ids(db, circle_id):
        if actor.is_admin:
            return "admin"
        raise forbidden("Only this circle's facilitator can view these fields.")
    if membership_status(db, circle_id, subject_id) not in ("member", "applicant"):
        raise not_found()
    return "facilitator"
