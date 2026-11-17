"""Directory and filter discovery (US-003, US-005). Also the AI fallback (MC-005)."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import Actor
from app.api.schemas.common import CircleCard, DiscoverResults, PersonCard
from app.db.models import Circle, CircleMembership
from app.services import people, policy


def circle_cards(db: Session, actor: Actor, circles: list[Circle]) -> list[CircleCard]:
    ids = [c.id for c in circles]
    counts: dict[UUID, int] = {}
    mine: dict[UUID, str] = {}
    if ids:
        counts = dict(
            db.execute(
                select(CircleMembership.circle_id, func.count())
                .where(CircleMembership.circle_id.in_(ids), CircleMembership.status == "member")
                .group_by(CircleMembership.circle_id)
            ).all()
        )
        mine = dict(
            db.execute(
                select(CircleMembership.circle_id, CircleMembership.status).where(
                    CircleMembership.circle_id.in_(ids), CircleMembership.user_id == actor.id
                )
            ).all()
        )
    facilitated = policy.facilitated_circle_ids(db, actor.id)
    cards = []
    for c in circles:
        show_count = policy.can_view_member_list(db, c, actor)
        cards.append(
            CircleCard(
                id=c.id,
                name=c.name,
                purpose=c.purpose,
                tags=c.tags,
                faith_tagged=c.faith_tagged,
                faith_context_label=c.faith_context_label if c.faith_tagged else None,
                community_tagged=c.community_tagged,
                community_label=c.community_label if c.community_tagged else None,
                admission_policy=c.admission_policy,
                meeting_mode=c.meeting_mode,
                area=c.area,
                member_count=counts.get(c.id, 0) if show_count else None,
                my_membership=mine.get(c.id, "none"),
                i_am_facilitator=c.id in facilitated,
            )
        )
    return cards


def all_circles(db: Session) -> list[Circle]:
    return list(db.scalars(select(Circle).order_by(Circle.name)))


def directory(db: Session, actor: Actor) -> list[PersonCard]:
    return people.person_cards(db, actor.id, policy.discoverable_ids(db, actor.id))


def _matches(
    card: PersonCard,
    stage: list[str] | None,
    interests: list[str] | None,
    challenges: list[str] | None,
    area: str | None,
    meeting_mode: str | None,
) -> bool:
    """Every applied filter must match, on public fields only: filtering on a hidden field
    would let a viewer infer it (MD-020)."""
    if stage and card.stage not in stage:
        return False
    if interests and not set(interests) <= set(card.interests):
        return False
    if challenges and not set(challenges) <= set(card.challenges):
        return False
    if area and card.area != area:
        return False
    if meeting_mode and meeting_mode != "either":
        if card.meeting_mode not in (meeting_mode, "either"):
            return False
    return True


def discover(
    db: Session,
    actor: Actor,
    *,
    stage: list[str] | None = None,
    interests: list[str] | None = None,
    challenges: list[str] | None = None,
    area: str | None = None,
    meeting_mode: str | None = None,
    circle_faith_tagged: bool | None = None,
) -> DiscoverResults:
    cards = [
        c
        for c in directory(db, actor)
        if _matches(c, stage, interests, challenges, area, meeting_mode)
    ]
    circles = []
    topics = set(interests or []) | set(challenges or [])
    for circle in all_circles(db):
        if circle_faith_tagged is not None and circle.faith_tagged != circle_faith_tagged:
            continue
        if topics and not topics <= set(circle.tags):
            continue
        if area and circle.area not in (area, None):
            continue
        if meeting_mode and meeting_mode != "either":
            if circle.meeting_mode not in (meeting_mode, "either", None):
                continue
        circles.append(circle)
    return DiscoverResults(people=cards, circles=circle_cards(db, actor, circles))
