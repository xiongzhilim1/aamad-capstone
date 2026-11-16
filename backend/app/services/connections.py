"""Requests, connections, contact sharing, blocks, reports, follow-ups (US-007-010, US-021)."""

from uuid import UUID

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.api.deps import Actor
from app.api.errors import ApiError, conflict, forbidden, not_found
from app.api.schemas.connections import (
    Block,
    Connection,
    ConnectionRequest,
    ContactSharing,
    FollowUp,
    FollowUpReport,
    ReportReceipt,
    RequestInbox,
)
from app.api.schemas.profile import ContactDetails
from app.db.models import (
    BlockRow,
    ConnectionRequestRow,
    ConnectionRow,
    ContactShare,
    FollowUpReportRow,
    ReportRow,
    User,
)
from app.services import people, policy


def _request_out(db: Session, row: ConnectionRequestRow, viewer_id: UUID) -> ConnectionRequest:
    outgoing = row.sender_id == viewer_id
    other = row.recipient_id if outgoing else row.sender_id
    return ConnectionRequest(
        id=row.id,
        direction="outgoing" if outgoing else "incoming",
        person=people.person_card(db, viewer_id, other),
        created_at=row.created_at,
    )


def inbox(db: Session, actor: Actor) -> RequestInbox:
    blocked = policy.blocked_ids(db, actor.id)
    rows = db.scalars(
        select(ConnectionRequestRow)
        .where(
            or_(
                ConnectionRequestRow.sender_id == actor.id,
                ConnectionRequestRow.recipient_id == actor.id,
            ),
            ConnectionRequestRow.status.in_(("pending", "declined")),
        )
        .order_by(ConnectionRequestRow.created_at.desc())
    ).all()
    incoming, outgoing = [], []
    for r in rows:
        if r.recipient_id == actor.id:
            if r.status == "pending" and r.sender_id not in blocked:
                incoming.append(_request_out(db, r, actor.id))
        elif not r.sender_hidden and r.recipient_id not in blocked:
            outgoing.append(_request_out(db, r, actor.id))
    return RequestInbox(incoming=incoming, outgoing=outgoing)


def send(db: Session, actor: Actor, recipient_id: UUID) -> ConnectionRequest:
    if recipient_id == actor.id:
        raise ApiError(422, "cannot_request_self", "You can't send a request to yourself.")
    # Not visible covers: unknown user, not opted in anywhere I can see, or blocked either
    # way. All three look the same to the sender (AC-001, AC-005; a block is never revealed).
    if recipient_id not in policy.visible_people_ids(db, actor.id):
        raise not_found("We couldn't find that person.")
    if recipient_id in policy.connected_ids(db, actor.id):
        raise conflict("already_connected", "You're already connected.")
    reverse = db.scalar(
        select(ConnectionRequestRow).where(
            ConnectionRequestRow.sender_id == recipient_id,
            ConnectionRequestRow.recipient_id == actor.id,
            ConnectionRequestRow.status == "pending",
        )
    )
    if reverse is not None:
        # Never auto-accept (PRD-v0 T04): the user answers the incoming request instead.
        raise conflict(
            "request_already_received",
            "They already asked to connect with you. Reply in Needs your reply.",
        )
    existing = db.scalar(
        select(ConnectionRequestRow).where(
            ConnectionRequestRow.sender_id == actor.id,
            ConnectionRequestRow.recipient_id == recipient_id,
            ConnectionRequestRow.status.in_(("pending", "declined")),
        )
    )
    if existing is not None:
        # Deduplicate. A declined request is reused silently, so a decline is not revealed
        # and the recipient is not asked again (OQ-06 default).
        existing.sender_hidden = False
        db.flush()
        return _request_out(db, existing, actor.id)
    row = ConnectionRequestRow(sender_id=actor.id, recipient_id=recipient_id)
    db.add(row)
    db.flush()
    db.refresh(row)
    return _request_out(db, row, actor.id)


def _own_open_request(db: Session, request_id: UUID, actor: Actor) -> ConnectionRequestRow:
    """Load a request the actor is party to; third parties get not-found (private pair data)."""
    row = db.get(ConnectionRequestRow, request_id)
    if row is None or actor.id not in (row.sender_id, row.recipient_id):
        raise not_found()
    return row


def withdraw(db: Session, actor: Actor, request_id: UUID) -> None:
    row = _own_open_request(db, request_id, actor)
    if row.sender_id != actor.id:
        raise forbidden("Only the sender can withdraw a request.")
    if row.status == "pending":
        row.status = "withdrawn"
        row.responded_at = policy.now()
    elif row.status == "declined":
        row.sender_hidden = True
    else:
        raise not_found()


def _recipient_pending(db: Session, request_id: UUID, actor: Actor) -> ConnectionRequestRow:
    row = _own_open_request(db, request_id, actor)
    if row.recipient_id != actor.id:
        raise forbidden("Only the person who received a request can answer it.")  # AC-003
    if row.status != "pending":
        raise not_found()
    return row


def accept(db: Session, actor: Actor, request_id: UUID) -> Connection:
    row = _recipient_pending(db, request_id, actor)
    if policy.is_blocked_pair(db, row.sender_id, row.recipient_id):
        raise not_found()
    row.status = "accepted"
    row.responded_at = policy.now()
    a, b = sorted((row.sender_id, row.recipient_id))
    conn = ConnectionRow(user_a=a, user_b=b, request_id=row.id)
    db.add(conn)
    db.flush()
    db.refresh(conn)
    return connection_out(db, conn, actor.id)


def decline(db: Session, actor: Actor, request_id: UUID) -> None:
    row = _recipient_pending(db, request_id, actor)
    row.status = "declined"
    row.responded_at = policy.now()


def connection_out(db: Session, conn: ConnectionRow, viewer_id: UUID) -> Connection:
    other = conn.user_b if conn.user_a == viewer_id else conn.user_a
    sharers = set(
        db.scalars(select(ContactShare.user_id).where(ContactShare.connection_id == conn.id))
    )
    blocked = policy.is_blocked_pair(db, viewer_id, other)
    mine = viewer_id in sharers
    theirs = other in sharers and not blocked
    contact = None
    if mine and theirs:  # both sides, and no block (MD-007, US-010 AC2)
        p = people.load_profile(db, other).profile
        contact = ContactDetails(
            email=p.contact_email, phone=p.contact_phone, other=p.contact_other
        )
    reports = db.scalars(
        select(FollowUpReportRow).where(FollowUpReportRow.connection_id == conn.id)
    ).all()
    follow_ups = []
    for number in (1, 2):
        mine_r = next(
            (r for r in reports if r.number == number and r.reporter_id == viewer_id), None
        )
        any_r = [r for r in reports if r.number == number]
        shown = mine_r or (any_r[0] if any_r else None)
        follow_ups.append(
            FollowUp(
                number=number,
                met=(any(r.met for r in any_r) if any_r else None),
                period_start=shown.period_start if shown else None,
                period_end=shown.period_end if shown else None,
                usefulness=mine_r.usefulness if mine_r else None,
                reported_by_me=mine_r is not None,
            )
        )
    return Connection(
        id=conn.id,
        person=people.person_card(db, viewer_id, other),
        connected_at=conn.created_at,
        contact_sharing=ContactSharing(mine=mine, theirs=theirs),
        their_contact=contact,
        follow_ups=follow_ups,
    )


def list_connections(db: Session, actor: Actor) -> list[Connection]:
    rows = db.scalars(
        select(ConnectionRow)
        .where(or_(ConnectionRow.user_a == actor.id, ConnectionRow.user_b == actor.id))
        .order_by(ConnectionRow.created_at.desc())
    ).all()
    return [connection_out(db, r, actor.id) for r in rows]


def set_contact_share(db: Session, actor: Actor, connection_id: UUID, share: bool) -> Connection:
    conn = policy.connection_for_member(db, connection_id, actor.id)
    row = db.get(ContactShare, (conn.id, actor.id))
    if share and row is None:
        db.add(ContactShare(connection_id=conn.id, user_id=actor.id))
    elif not share and row is not None:
        db.delete(row)
    db.flush()
    return connection_out(db, conn, actor.id)


def report_follow_up(
    db: Session, actor: Actor, connection_id: UUID, number: int, body: FollowUpReport
) -> Connection:
    conn = policy.connection_for_member(db, connection_id, actor.id)
    if body.period_start and body.period_end and body.period_end < body.period_start:
        raise ApiError(422, "validation_error", "The end date is before the start date.")
    row = db.get(FollowUpReportRow, (conn.id, number, actor.id))
    if row is None:
        row = FollowUpReportRow(
            connection_id=conn.id, number=number, reporter_id=actor.id, met=False
        )
        db.add(row)
    row.met = body.met
    row.period_start, row.period_end = body.period_start, body.period_end
    row.usefulness = body.usefulness
    row.updated_at = policy.now()
    db.flush()
    return connection_out(db, conn, actor.id)


def _existing_user(db: Session, user_id: UUID, actor: Actor) -> User:
    user = db.get(User, user_id)
    if user is None or user.id == actor.id:
        raise not_found("We couldn't find that person.")
    return user


def block(db: Session, actor: Actor, user_id: UUID) -> Block:
    user = _existing_user(db, user_id, actor)
    row = db.get(BlockRow, (actor.id, user_id))
    if row is None:
        row = BlockRow(blocker_id=actor.id, blocked_id=user_id)
        db.add(row)
        # Pending requests between the two are closed; the other side is not told.
        for r in db.scalars(
            select(ConnectionRequestRow).where(
                ConnectionRequestRow.status == "pending",
                or_(
                    (ConnectionRequestRow.sender_id == actor.id)
                    & (ConnectionRequestRow.recipient_id == user_id),
                    (ConnectionRequestRow.sender_id == user_id)
                    & (ConnectionRequestRow.recipient_id == actor.id),
                ),
            )
        ):
            r.status = "withdrawn" if r.sender_id == actor.id else "declined"
            r.responded_at = policy.now()
        db.flush()
        db.refresh(row)
    return Block(person=people.refs(db, [user.id])[user.id], created_at=row.created_at)


def unblock(db: Session, actor: Actor, user_id: UUID) -> None:
    db.execute(
        delete(BlockRow).where(BlockRow.blocker_id == actor.id, BlockRow.blocked_id == user_id)
    )


def list_blocks(db: Session, actor: Actor) -> list[Block]:
    rows = db.scalars(
        select(BlockRow).where(BlockRow.blocker_id == actor.id).order_by(BlockRow.created_at.desc())
    ).all()
    names = people.refs(db, [r.blocked_id for r in rows])
    return [Block(person=names[r.blocked_id], created_at=r.created_at) for r in rows]


def report(db: Session, actor: Actor, subject_id: UUID, reason: str) -> ReportReceipt:
    _existing_user(db, subject_id, actor)
    row = ReportRow(reporter_id=actor.id, subject_id=subject_id, reason=reason)
    db.add(row)
    db.flush()
    db.refresh(row)
    return ReportReceipt(id=row.id, created_at=row.created_at)
