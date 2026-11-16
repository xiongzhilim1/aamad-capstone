"""Circles (US-011, US-016, US-017)."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import Actor
from app.api.errors import ApiError, not_found
from app.api.schemas.circles import (
    Applicant,
    CircleCreate,
    CircleDetail,
    CircleUpdate,
    LinkedEvent,
    MembershipResult,
)
from app.api.schemas.common import CircleCard
from app.db.models import Circle, CircleFacilitator, CircleMembership, Event, Profile, User
from app.services import discovery, people, policy


def _circle(db: Session, circle_id: UUID) -> Circle:
    circle = db.get(Circle, circle_id)
    if circle is None:
        raise not_found()
    return circle


def list_circles(
    db: Session, actor: Actor, faith_tagged: bool | None, mine: bool
) -> list[CircleCard]:
    circles = discovery.all_circles(db)
    if faith_tagged is not None:
        circles = [c for c in circles if c.faith_tagged == faith_tagged]
    cards = discovery.circle_cards(db, actor, circles)
    if mine:
        cards = [c for c in cards if c.my_membership != "none" or c.i_am_facilitator]
    return cards


def detail(db: Session, actor: Actor, circle_id: UUID) -> CircleDetail:
    circle = _circle(db, circle_id)
    card = discovery.circle_cards(db, actor, [circle])[0]
    manage = policy.can_manage_circle(db, circle.id, actor)
    members = None
    if policy.can_view_member_list(db, circle, actor):
        ids = set(
            db.scalars(
                select(CircleMembership.user_id).where(
                    CircleMembership.circle_id == circle.id, CircleMembership.status == "member"
                )
            )
        )
        if not manage:
            ids -= policy.blocked_ids(db, actor.id)
        members = sorted(people.refs(db, ids).values(), key=lambda r: r.display_name.lower())
    events = db.scalars(
        select(Event)
        .where(Event.circle_id == circle.id, Event.state == "approved")
        .order_by(Event.starts_at)
    ).all()
    pending = None
    if manage:
        pending = db.scalar(
            select(func.count()).where(
                CircleMembership.circle_id == circle.id, CircleMembership.status == "applicant"
            )
        )
    facilitators = people.refs(db, policy.facilitator_ids(db, circle.id)).values()
    return CircleDetail(
        **card.model_dump(),
        facilitators=sorted(facilitators, key=lambda r: r.display_name.lower()),
        member_list_visibility=circle.member_list_visibility,
        members=members,
        linked_events=[LinkedEvent(id=e.id, title=e.title, starts_at=e.starts_at) for e in events],
        pending_applications=pending,
    )


def _check_faith(tagged: bool, label: str | None) -> None:
    if label and not tagged:
        raise ApiError(422, "validation_error", "A faith label needs the faith tag turned on.")


def create(db: Session, actor: Actor, body: CircleCreate) -> CircleDetail:
    if db.get(User, body.facilitator_id) is None:
        raise not_found("We couldn't find that person.")
    _check_faith(body.faith_tagged, body.faith_context_label)
    data = body.model_dump(mode="json", exclude={"facilitator_id"})
    circle = Circle(**data)
    db.add(circle)
    db.flush()
    db.add(CircleFacilitator(circle_id=circle.id, user_id=body.facilitator_id))
    db.flush()
    return detail(db, actor, circle.id)


def update(db: Session, actor: Actor, circle_id: UUID, body: CircleUpdate) -> CircleDetail:
    circle = policy.managed_circle(db, circle_id, actor)
    for key, value in body.model_dump(mode="json", exclude_unset=True).items():
        setattr(circle, key, value)
    if not circle.faith_tagged:
        circle.faith_context_label = None
    db.flush()
    return detail(db, actor, circle.id)


def join(db: Session, actor: Actor, circle_id: UUID) -> MembershipResult:
    """Writes a membership row only. Never touches the profile, so joining a faith-tagged
    circle records no faith data about the person (MN-004, US-017 AC4)."""
    circle = _circle(db, circle_id)
    row = db.get(CircleMembership, (circle.id, actor.id))
    if row is None:
        status = "member" if circle.admission_policy == "open" else "applicant"
        row = CircleMembership(circle_id=circle.id, user_id=actor.id, status=status)
        db.add(row)
        db.flush()
    return MembershipResult(circle_id=circle.id, membership=row.status)


def leave(db: Session, actor: Actor, circle_id: UUID) -> None:
    circle = _circle(db, circle_id)
    row = db.get(CircleMembership, (circle.id, actor.id))
    if row is not None:
        db.delete(row)


def applications(db: Session, actor: Actor, circle_id: UUID) -> list[Applicant]:
    circle = policy.managed_circle(db, circle_id, actor)
    rows = db.execute(
        select(CircleMembership, User, Profile)
        .join(User, User.id == CircleMembership.user_id)
        .join(Profile, Profile.user_id == User.id)
        .where(CircleMembership.circle_id == circle.id, CircleMembership.status == "applicant")
        .order_by(CircleMembership.created_at)
    ).all()
    return [
        Applicant(user_id=u.id, display_name=u.display_name, stage=p.stage, applied_at=m.created_at)
        for m, u, p in rows
    ]


def _applicant(db: Session, actor: Actor, circle_id: UUID, user_id: UUID) -> CircleMembership:
    circle = policy.managed_circle(db, circle_id, actor)
    row = db.get(CircleMembership, (circle.id, user_id))
    if row is None or row.status != "applicant":
        raise not_found()
    return row


def approve(db: Session, actor: Actor, circle_id: UUID, user_id: UUID) -> MembershipResult:
    row = _applicant(db, actor, circle_id, user_id)
    row.status = "member"
    db.flush()
    return MembershipResult(circle_id=circle_id, membership="member")


def decline(db: Session, actor: Actor, circle_id: UUID, user_id: UUID) -> None:
    db.delete(_applicant(db, actor, circle_id, user_id))
