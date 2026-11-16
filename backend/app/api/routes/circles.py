"""Circles (US-011, US-016, US-017)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.api.deps import AdminActor, CurrentActor
from app.api.errors import error_responses
from app.api.schemas.circles import (
    Applicant,
    CircleCreate,
    CircleDetail,
    CircleUpdate,
    MembershipResult,
)
from app.api.schemas.common import CircleCard
from app.api.schemas.profile import MatchingFieldsView
from app.db.session import Db
from app.services import circles, people, policy

router = APIRouter(prefix="/circles", tags=["circles"], responses=error_responses(401))


@router.get("", response_model=list[CircleCard], summary="Browse circles")
def list_circles(
    actor: CurrentActor,
    db: Db,
    faith_tagged: Annotated[bool | None, Query(description="Filter by the faith tag.")] = None,
    mine: Annotated[bool, Query(description="Only circles I belong to or applied to.")] = False,
) -> list[CircleCard]:
    return circles.list_circles(db, actor, faith_tagged, mine)


@router.post(
    "",
    response_model=CircleDetail,
    status_code=201,
    responses=error_responses(403, 404, 422),
    summary="Create a circle (admin)",
)
def create_circle(body: CircleCreate, actor: AdminActor, db: Db) -> CircleDetail:
    return circles.create(db, actor, body)


@router.get(
    "/{circle_id}", response_model=CircleDetail, responses=error_responses(404), summary="A circle"
)
def get_circle(circle_id: UUID, actor: CurrentActor, db: Db) -> CircleDetail:
    return circles.detail(db, actor, circle_id)


@router.patch(
    "/{circle_id}",
    response_model=CircleDetail,
    responses=error_responses(403, 404, 422),
    summary="Edit a circle (facilitator or admin)",
)
def update_circle(circle_id: UUID, body: CircleUpdate, actor: CurrentActor, db: Db) -> CircleDetail:
    return circles.update(db, actor, circle_id, body)


@router.post(
    "/{circle_id}/join",
    response_model=MembershipResult,
    responses=error_responses(404),
    summary="Join, or ask to join",
)
def join_circle(circle_id: UUID, actor: CurrentActor, db: Db) -> MembershipResult:
    """Open circles: member at once. Approval circles: applicant until approved (AC-011)."""
    return circles.join(db, actor, circle_id)


@router.delete(
    "/{circle_id}/membership",
    status_code=204,
    responses=error_responses(404),
    summary="Leave, or withdraw my application",
)
def leave_circle(circle_id: UUID, actor: CurrentActor, db: Db) -> Response:
    circles.leave(db, actor, circle_id)
    return Response(status_code=204)


@router.get(
    "/{circle_id}/applications",
    response_model=list[Applicant],
    responses=error_responses(403, 404),
    summary="Pending applicants (facilitator or admin)",
)
def list_applications(circle_id: UUID, actor: CurrentActor, db: Db) -> list[Applicant]:
    return circles.applications(db, actor, circle_id)


@router.post(
    "/{circle_id}/applications/{user_id}/approve",
    response_model=MembershipResult,
    responses=error_responses(403, 404),
    summary="Approve an applicant",
)
def approve_application(
    circle_id: UUID, user_id: UUID, actor: CurrentActor, db: Db
) -> MembershipResult:
    return circles.approve(db, actor, circle_id, user_id)


@router.post(
    "/{circle_id}/applications/{user_id}/decline",
    status_code=204,
    responses=error_responses(403, 404),
    summary="Decline an applicant",
)
def decline_application(circle_id: UUID, user_id: UUID, actor: CurrentActor, db: Db) -> Response:
    circles.decline(db, actor, circle_id, user_id)
    return Response(status_code=204)


@router.get(
    "/{circle_id}/members/{user_id}/matching-fields",
    response_model=MatchingFieldsView,
    responses=error_responses(403, 404),
    summary="A member's or applicant's Private: matching fields (facilitator)",
)
def get_member_matching_fields(
    circle_id: UUID, user_id: UUID, actor: CurrentActor, db: Db
) -> MatchingFieldsView:
    """Own-circle facilitators only, for members and pending applicants. Every view is logged;
    if the log cannot be written, nothing is returned (MD-022, CR-016, AC-020)."""
    role = policy.staff_scope(db, actor, user_id, circle_id)
    return people.matching_fields_view(db, actor.id, role, user_id, circle_id)
