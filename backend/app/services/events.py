"""Events, registration, attendance, late attendance and reconnection.

US-004, US-012 to US-015, US-018 to US-020, US-025. Registration, attendance and membership
are separate facts (MD-012, MN-007); only confirmed attendance unlocks reconnection (CR-017).
"""

import hmac
from datetime import timedelta
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.api.deps import Actor
from app.api.errors import ApiError, conflict, forbidden, not_found
from app.api.schemas.common import PersonRef
from app.api.schemas.events import (
    AttendanceClaim,
    AttendanceCounts,
    AttendanceResult,
    AttendanceRow,
    CheckinCodeIssued,
    CheckinCodeState,
    EventApproval,
    EventCard,
    EventDetail,
    EventWrite,
    HostAttendance,
    MyEventStatus,
    ReconnectList,
    RegistrationResult,
    Venue,
    VenueWrite,
)
from app.db.models import (
    Attendance,
    AttendanceLog,
    CheckinAttempt,
    Circle,
    DiscoveryConsent,
    Event,
    EventApprovalRow,
    EventCheckinCode,
    EventHost,
    Registration,
    User,
    VenueRow,
)
from app.security import hash_event_code, new_event_code
from app.services import people, policy

CODE_WINDOW = timedelta(days=7)  # MD-024 (OQ-12 proposed value)
MAX_WRONG_CODES_PER_HOUR = 5


# --- output ----------------------------------------------------------------------------


def venue_out(v: VenueRow) -> Venue:
    return Venue(
        id=v.id,
        name=v.name,
        area=v.area,
        address_hint=v.address_hint,
        capacity=v.capacity,
        notes=v.notes,
        synthetic=v.synthetic,
    )


def _my_status(db: Session, event: Event, actor: Actor) -> MyEventStatus:
    att = db.scalar(
        select(Attendance).where(Attendance.event_id == event.id, Attendance.user_id == actor.id)
    )
    consent = db.scalar(
        select(DiscoveryConsent.id).where(
            DiscoveryConsent.event_id == event.id, DiscoveryConsent.user_id == actor.id
        )
    )
    return MyEventStatus(
        registered=db.get(Registration, (event.id, actor.id)) is not None,
        attendance=att.status if att else "none",
        attendance_source=att.source if att else None,
        reconnect_opted_in=consent is not None,
        can_manage=policy.can_manage_event(db, event, actor.id),
        is_organiser=event.organiser_id == actor.id,
    )


def _card_fields(db: Session, event: Event, actor: Actor) -> dict[str, object]:
    venue = db.get(VenueRow, event.venue_id) if event.venue_id else None
    return {
        "id": event.id,
        "title": event.title,
        "starts_at": event.starts_at,
        "ends_at": event.ends_at,
        "timezone": event.timezone,
        "mode": event.mode,
        "venue_name": venue.name if venue else event.venue_text,
        "price_amount": event.price_amount,
        "price_currency": event.price_currency,
        "state": event.state,
        "added_after_event": event.added_after_event,
        "has_ended": policy.has_ended(event),
        "my": _my_status(db, event, actor),
    }


def card(db: Session, event: Event, actor: Actor) -> EventCard:
    return EventCard(**_card_fields(db, event, actor))


def detail(db: Session, event: Event, actor: Actor) -> EventDetail:
    venue = db.get(VenueRow, event.venue_id) if event.venue_id else None
    circle = db.get(Circle, event.circle_id) if event.circle_id else None
    co_hosts = policy.co_host_ids(db, event.id)
    names = people.refs(db, {event.organiser_id, *co_hosts})
    staff = actor.is_admin or policy.can_manage_event(db, event, actor.id)
    approvals = None
    if staff:
        rows = db.scalars(
            select(EventApprovalRow)
            .where(EventApprovalRow.event_id == event.id)
            .order_by(EventApprovalRow.decided_at)
        ).all()
        admins = people.refs(db, [r.admin_id for r in rows])
        approvals = [
            EventApproval(
                admin=admins[r.admin_id],
                decision=r.decision,
                reason=r.reason,
                decided_at=r.decided_at,
            )
            for r in rows
        ]
    registered = db.scalar(select(func.count()).where(Registration.event_id == event.id)) or 0
    return EventDetail(
        **_card_fields(db, event, actor),
        description=event.description,
        venue=venue_out(venue) if venue else None,
        venue_text=event.venue_text,
        capacity=event.capacity,
        includes=event.includes,
        organiser=names[event.organiser_id],
        co_hosts=sorted((names[i] for i in co_hosts), key=lambda r: r.display_name.lower()),
        circle=PersonRef(id=circle.id, display_name=circle.name) if circle else None,
        registered_count=registered,
        approvals=approvals,
    )


# --- listing and drafting (US-012) -----------------------------------------------------


def list_published(db: Session, actor: Actor, when: str) -> list[EventCard]:
    stmt = select(Event).where(Event.state == "approved")  # MN-005
    if when == "upcoming":
        stmt = stmt.where(Event.ends_at > policy.now())
    elif when == "past":
        stmt = stmt.where(Event.ends_at <= policy.now())
    return [card(db, e, actor) for e in db.scalars(stmt.order_by(Event.starts_at))]


def list_mine(db: Session, actor: Actor) -> list[EventCard]:
    hosted = select(EventHost.event_id).where(EventHost.user_id == actor.id)
    stmt = select(Event).where((Event.organiser_id == actor.id) | Event.id.in_(hosted))
    return [card(db, e, actor) for e in db.scalars(stmt.order_by(Event.starts_at.desc()))]


def _apply(db: Session, event: Event, body: EventWrite) -> None:
    if body.starts_at.tzinfo is None or body.ends_at.tzinfo is None:
        raise ApiError(422, "validation_error", "Give the start and end with a time zone.")
    if body.ends_at <= body.starts_at:
        raise ApiError(422, "validation_error", "The end must be after the start.")
    if (body.price_amount is None) != (body.price_currency is None):
        raise ApiError(422, "validation_error", "Give a price and its currency together.")
    if body.venue_id and db.get(VenueRow, body.venue_id) is None:
        raise not_found("We couldn't find that venue.")
    if body.circle_id and db.get(Circle, body.circle_id) is None:
        raise not_found("We couldn't find that circle.")
    for key, value in body.model_dump().items():
        setattr(event, key, value)
    event.mode = body.mode.value
    event.updated_at = policy.now()


def create(db: Session, actor: Actor, body: EventWrite) -> EventDetail:
    if not actor.is_organiser:
        raise forbidden("Only organisers can create events.")
    event = Event(organiser_id=actor.id, state="draft")
    _apply(db, event, body)
    event.added_after_event = body.starts_at <= policy.now()  # MD-025
    db.add(event)
    db.flush()
    db.refresh(event)
    return detail(db, event, actor)


def update(db: Session, actor: Actor, event_id: UUID, body: EventWrite) -> EventDetail:
    event = policy.managed_event(db, event_id, actor)
    if event.state not in ("draft", "rejected"):
        raise conflict("not_editable", "Withdraw the submission before editing this event.")
    _apply(db, event, body)
    event.state = "draft"
    db.flush()
    return detail(db, event, actor)


def _transition(
    db: Session, actor: Actor, event_id: UUID, allowed: tuple[str, ...], to: str
) -> EventDetail:
    event = policy.organised_event(db, event_id, actor)
    if event.state not in allowed:
        raise conflict("invalid_state", f"This event is {event.state}, so that isn't possible.")
    event.state = to
    event.updated_at = policy.now()
    db.flush()
    return detail(db, event, actor)


def submit(db: Session, actor: Actor, event_id: UUID) -> EventDetail:
    return _transition(db, actor, event_id, ("draft", "rejected"), "submitted")


def withdraw_submission(db: Session, actor: Actor, event_id: UUID) -> EventDetail:
    return _transition(db, actor, event_id, ("submitted",), "draft")


def cancel(db: Session, actor: Actor, event_id: UUID) -> EventDetail:
    event = policy.visible_event(db, event_id, actor)
    if not (actor.is_admin or event.organiser_id == actor.id):
        raise forbidden("Only the organiser or the admin can cancel an event.")
    if event.state != "approved":
        raise conflict("invalid_state", "Only a published event can be cancelled.")
    event.state = "cancelled"
    event.updated_at = policy.now()
    db.flush()
    return detail(db, event, actor)


def decide(
    db: Session, actor: Actor, event_id: UUID, decision: str, reason: str | None
) -> EventDetail:
    """The only code path that sets `approved`, and it always writes the decision row in the
    same transaction (CR-014, AC-006). Callers must have passed the admin dependency."""
    if not actor.is_admin:
        raise forbidden("Only the admin can do that.")
    event = db.get(Event, event_id)
    if event is None:
        raise not_found()
    if event.state != "submitted":
        raise conflict("invalid_state", "Only a submitted event can be decided.")
    db.add(EventApprovalRow(event_id=event.id, admin_id=actor.id, decision=decision, reason=reason))
    event.state = "approved" if decision == "approve" else "rejected"
    event.updated_at = policy.now()
    db.flush()
    return detail(db, event, actor)


def queue(db: Session, actor: Actor) -> list[EventDetail]:
    rows = db.scalars(select(Event).where(Event.state == "submitted").order_by(Event.updated_at))
    return [detail(db, e, actor) for e in rows]


def set_co_host(db: Session, actor: Actor, event_id: UUID, user_id: UUID, add: bool) -> EventDetail:
    event = policy.organised_event(db, event_id, actor)
    if db.get(User, user_id) is None or user_id == event.organiser_id:
        raise not_found("We couldn't find that person.")
    row = db.get(EventHost, (event.id, user_id))
    if add and row is None:
        db.add(EventHost(event_id=event.id, user_id=user_id))
    elif not add and row is not None:
        db.delete(row)
    db.flush()
    return detail(db, event, actor)


# --- registration (US-014) -------------------------------------------------------------


def register(db: Session, actor: Actor, event_id: UUID) -> RegistrationResult:
    event = policy.published_event(db, event_id, actor)
    if policy.has_ended(event):
        raise conflict("event_ended", "This event has ended. Were you there? Use I was there.")
    if db.get(Registration, (event.id, actor.id)) is None:
        db.add(Registration(event_id=event.id, user_id=actor.id))
        db.flush()
    return RegistrationResult(event_id=event.id, registered=True)


def unregister(db: Session, actor: Actor, event_id: UUID) -> RegistrationResult:
    event = policy.published_event(db, event_id, actor)
    row = db.get(Registration, (event.id, actor.id))
    if row is not None:
        db.delete(row)
    return RegistrationResult(event_id=event.id, registered=False)


# --- attendance (US-015, US-025) -------------------------------------------------------


def _attendance(db: Session, event_id: UUID, user_id: UUID) -> Attendance | None:
    return db.scalar(
        select(Attendance).where(Attendance.event_id == event_id, Attendance.user_id == user_id)
    )


def _set_attendance(
    db: Session, event: Event, user_id: UUID, status: str, source: str, actor_id: UUID
) -> Attendance | None:
    """Single writer for attendance. Logs every change; leaving `confirmed` also removes the
    person's reconnection consent for this event, so they drop off the list at once."""
    row = _attendance(db, event.id, user_id)
    before = row.status if row else "none"
    if before == status:
        return row
    db.add(
        AttendanceLog(
            event_id=event.id,
            user_id=user_id,
            from_status=before,
            to_status=status,
            actor_id=actor_id,
        )
    )
    if status != "confirmed":
        db.execute(
            delete(DiscoveryConsent).where(
                DiscoveryConsent.event_id == event.id, DiscoveryConsent.user_id == user_id
            )
        )
    if status == "none":
        if row is not None:
            db.delete(row)
        db.flush()
        return None
    if row is None:
        row = Attendance(event_id=event.id, user_id=user_id, status=status, source=source)
        db.add(row)
    else:
        row.status, row.source, row.updated_at = status, source, policy.now()
    db.flush()
    return row


def _result(event: Event, row: Attendance | None) -> AttendanceResult:
    return AttendanceResult(
        event_id=event.id,
        attendance=row.status if row else "none",
        attendance_source=row.source if row else None,
    )


def _started_host_event(db: Session, actor: Actor, event_id: UUID) -> Event:
    event = policy.managed_event(db, event_id, actor)
    if event.state != "approved":
        raise conflict("invalid_state", "Attendance opens once the event is published.")
    if not policy.has_started(event):
        raise conflict("event_not_started", "Attendance opens when the event starts.")
    return event


def host_attendance(db: Session, actor: Actor, event_id: UUID) -> HostAttendance:
    event = policy.managed_event(db, event_id, actor)
    regs = {
        r.user_id: r
        for r in db.scalars(select(Registration).where(Registration.event_id == event.id))
    }
    atts = {
        a.user_id: a for a in db.scalars(select(Attendance).where(Attendance.event_id == event.id))
    }
    names = people.refs(db, set(regs) | set(atts))

    def row(uid: UUID) -> AttendanceRow:
        att, reg = atts.get(uid), regs.get(uid)
        return AttendanceRow(
            user_id=uid,
            display_name=names[uid].display_name,
            registered=reg is not None,
            registered_at=reg.created_at if reg else None,
            attendance=att.status if att else "none",
            source=att.source if att else None,
            updated_at=att.updated_at if att else None,
        )

    listed = set(regs) | {u for u, a in atts.items() if a.source == "organiser"}
    confirmed = [a for a in atts.values() if a.status == "confirmed"]
    code = db.get(EventCheckinCode, event.id)
    return HostAttendance(
        people=sorted((row(u) for u in listed), key=lambda r: r.display_name.lower()),
        claims=[
            AttendanceClaim(
                claim_id=a.id,
                user_id=a.user_id,
                display_name=names[a.user_id].display_name,
                claimed_at=a.created_at,
            )
            for a in sorted(atts.values(), key=lambda a: a.created_at)
            if a.status == "claimed"
        ],
        joined_by_code=sorted(
            (row(a.user_id) for a in confirmed if a.source == "code"),
            key=lambda r: r.display_name.lower(),
        ),
        counts=AttendanceCounts(
            registered=len(regs),
            confirmed=len(confirmed),
            confirmed_by_organiser=sum(a.source == "organiser" for a in confirmed),
            confirmed_by_claim=sum(a.source == "claim" for a in confirmed),
            confirmed_by_code=sum(a.source == "code" for a in confirmed),
            claims_pending=sum(a.status == "claimed" for a in atts.values()),
        ),
        checkin_code=CheckinCodeState(
            active=bool(code and code.active), valid_until=code.valid_until if code else None
        ),
    )


def mark(
    db: Session, actor: Actor, event_id: UUID, user_id: UUID, attended: bool
) -> HostAttendance:
    event = _started_host_event(db, actor, event_id)
    existing = _attendance(db, event.id, user_id)
    if db.get(Registration, (event.id, user_id)) is None and existing is None:
        raise not_found("That person isn't on this event's list.")
    if attended:
        _set_attendance(db, event, user_id, "confirmed", "organiser", actor.id)
    else:
        _set_attendance(db, event, user_id, "none", "organiser", actor.id)
    return host_attendance(db, actor, event_id)


def _claimable_event(db: Session, actor: Actor, event_id: UUID) -> Event:
    event = policy.published_event(db, event_id, actor)  # MN-017: approved events only
    if not policy.has_started(event):
        raise conflict("event_not_started", "This event hasn't started yet.")
    return event


def claim(db: Session, actor: Actor, event_id: UUID) -> AttendanceResult:
    event = _claimable_event(db, actor, event_id)
    row = _attendance(db, event.id, actor.id)
    if row is None:
        row = _set_attendance(db, event, actor.id, "claimed", "claim", actor.id)
    return _result(event, row)


def withdraw_claim(db: Session, actor: Actor, event_id: UUID) -> AttendanceResult:
    event = policy.published_event(db, event_id, actor)
    row = _attendance(db, event.id, actor.id)
    if row is not None and row.status == "claimed":
        row = _set_attendance(db, event, actor.id, "none", "claim", actor.id)
    return _result(event, row)


def decide_claim(
    db: Session, actor: Actor, event_id: UUID, claim_id: UUID, approve: bool
) -> HostAttendance:
    event = _started_host_event(db, actor, event_id)
    row = db.get(Attendance, claim_id)
    if row is None or row.event_id != event.id or row.status != "claimed":
        raise not_found()
    _set_attendance(
        db, event, row.user_id, "confirmed" if approve else "declined", "claim", actor.id
    )
    return host_attendance(db, actor, event_id)


def rotate_code(db: Session, actor: Actor, event_id: UUID) -> CheckinCodeIssued:
    event = policy.managed_event(db, event_id, actor)
    if event.state != "approved":
        raise conflict("invalid_state", "The event code is available once the event is published.")
    code = new_event_code()
    row = db.get(EventCheckinCode, event.id)
    if row is None:
        row = EventCheckinCode(event_id=event.id, code_hash="", valid_until=event.ends_at)
        db.add(row)
    row.code_hash = hash_event_code(event.id, code)
    row.valid_until = event.ends_at + CODE_WINDOW
    row.active = True
    row.rotated_at = policy.now()
    db.flush()
    return CheckinCodeIssued(active=True, valid_until=row.valid_until, code=code)


def disable_code(db: Session, actor: Actor, event_id: UUID) -> None:
    event = policy.managed_event(db, event_id, actor)
    row = db.get(EventCheckinCode, event.id)
    if row is not None:
        row.active = False


def checkin(db: Session, actor: Actor, event_id: UUID, code: str) -> AttendanceResult:
    """Event-code entry (MD-024, CR-017). Fails closed: every failure confirms nothing.

    Failed attempts are committed even though the request errors, so the limit cannot be
    bypassed by the rollback.
    """
    since = policy.now() - timedelta(hours=1)
    recent = db.scalars(
        select(CheckinAttempt.created_at)
        .where(
            CheckinAttempt.user_id == actor.id,
            CheckinAttempt.succeeded.is_(False),
            CheckinAttempt.created_at > since,
        )
        .order_by(CheckinAttempt.created_at)
    ).all()
    if len(recent) >= MAX_WRONG_CODES_PER_HOUR:
        raise ApiError(
            429,
            "rate_limited",
            "Too many tries. Try again later, or ask the host to confirm.",
            retry_at=recent[-MAX_WRONG_CODES_PER_HOUR] + timedelta(hours=1),
        )
    event = _claimable_event(db, actor, event_id)
    row = db.get(EventCheckinCode, event.id)
    failure: ApiError | None = None
    if row is None or not row.active:
        failure = ApiError(
            422, "code_invalid", "That code didn't work. Check with the host for the current code."
        )
    elif policy.now() > row.valid_until:
        failure = ApiError(422, "code_expired", "This event's code has expired.")
    elif not hmac.compare_digest(row.code_hash, hash_event_code(event.id, code)):
        failure = ApiError(
            422, "code_invalid", "That code didn't work. Check with the host for the current code."
        )
    db.add(CheckinAttempt(user_id=actor.id, event_id=event.id, succeeded=failure is None))
    if failure is not None:
        db.commit()
        raise failure
    att = _attendance(db, event.id, actor.id)
    if att is None or att.status != "confirmed":
        att = _set_attendance(db, event, actor.id, "confirmed", "code", actor.id)
    return _result(event, att)


# --- reconnection (US-004) -------------------------------------------------------------


def _confirmed_ended(db: Session, actor: Actor, event_id: UUID) -> Event:
    event = policy.published_event(db, event_id, actor)
    if not policy.has_confirmed_attendance(db, event.id, actor.id):
        raise forbidden(
            "Were you at this event? Enter the code the host shared, or ask the host to confirm.",
            "attendance_not_confirmed",
        )
    if not policy.has_ended(event):
        raise conflict("event_not_ended", "Reconnection opens after the event ends.")
    return event


def set_reconnect_consent(db: Session, actor: Actor, event_id: UUID, opted_in: bool) -> EventDetail:
    """Per-event consent only: the global directory consent is a different row (MN-001)."""
    event = _confirmed_ended(db, actor, event_id)
    row = db.scalar(
        select(DiscoveryConsent).where(
            DiscoveryConsent.event_id == event.id, DiscoveryConsent.user_id == actor.id
        )
    )
    if opted_in and row is None:
        db.add(DiscoveryConsent(user_id=actor.id, event_id=event.id))
    elif not opted_in and row is not None:
        db.delete(row)
    db.flush()
    return detail(db, event, actor)


def reconnect_list(db: Session, actor: Actor, event_id: UUID) -> ReconnectList:
    event = _confirmed_ended(db, actor, event_id)
    members = policy.reconnect_member_ids(db, event.id)
    if actor.id not in members:
        raise forbidden(
            "Opt in to see who else from this event opted in.", "reconnect_not_opted_in"
        )
    ids = members - {actor.id} - policy.blocked_ids(db, actor.id)
    return ReconnectList(event_id=event.id, people=people.person_cards(db, actor.id, ids))


# --- venues (US-020) -------------------------------------------------------------------


def list_venues(db: Session) -> list[Venue]:
    return [venue_out(v) for v in db.scalars(select(VenueRow).order_by(VenueRow.name))]


def save_venue(db: Session, venue_id: UUID | None, body: VenueWrite) -> Venue:
    if venue_id is None:
        row = VenueRow(synthetic=True)
        db.add(row)
    else:
        found = db.get(VenueRow, venue_id)
        if found is None:
            raise not_found()
        row = found
    for key, value in body.model_dump().items():
        setattr(row, key, value or None)
    db.flush()
    return venue_out(row)


def delete_venue(db: Session, venue_id: UUID) -> None:
    row = db.get(VenueRow, venue_id)
    if row is None:
        raise not_found()
    db.delete(row)
