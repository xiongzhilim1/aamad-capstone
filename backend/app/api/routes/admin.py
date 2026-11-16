"""Admin: event gate, reports, roles, venues, staff access, metrics (US-010/013/020/022)."""

from uuid import UUID

from fastapi import APIRouter, Response

from app.api.deps import AdminActor
from app.api.errors import error_responses
from app.api.schemas.admin import AccessLogEntry, AdminUser, Metrics, Report, RoleUpdate
from app.api.schemas.events import EventDecisionRequest, EventDetail, Venue, VenueWrite
from app.api.schemas.profile import MatchingFieldsView
from app.db.session import Db
from app.services import admin, events, people, policy

router = APIRouter(prefix="/admin", tags=["admin"], responses=error_responses(401, 403))


@router.get("/events/queue", response_model=list[EventDetail], summary="Submitted events")
def event_queue(actor: AdminActor, db: Db) -> list[EventDetail]:
    return events.queue(db, actor)


@router.post(
    "/events/{event_id}/decision",
    response_model=EventDetail,
    responses=error_responses(404, 409, 422),
    summary="Approve or reject an event",
)
def decide_event(
    event_id: UUID, body: EventDecisionRequest, actor: AdminActor, db: Db
) -> EventDetail:
    """The only path that publishes an event. Stores admin, time and decision (AC-006, MP-002)."""
    return events.decide(db, actor, event_id, body.decision.value, body.reason)


@router.get("/reports", response_model=list[Report], summary="Reports from participants")
def list_reports(actor: AdminActor, db: Db) -> list[Report]:
    return admin.list_reports(db)


@router.get("/users", response_model=list[AdminUser], summary="Users and roles")
def list_users(actor: AdminActor, db: Db) -> list[AdminUser]:
    return admin.list_users(db)


@router.put(
    "/users/{user_id}/roles",
    response_model=AdminUser,
    responses=error_responses(404, 422),
    summary="Grant or remove the organiser role",
)
def put_roles(user_id: UUID, body: RoleUpdate, actor: AdminActor, db: Db) -> AdminUser:
    return admin.set_organiser(db, user_id, body.organiser)


@router.get(
    "/users/{user_id}/matching-fields",
    response_model=MatchingFieldsView,
    responses=error_responses(404),
    summary="A participant's Private: matching fields",
)
def get_user_matching_fields(user_id: UUID, actor: AdminActor, db: Db) -> MatchingFieldsView:
    """Logged on every view (MD-022, CR-016)."""
    role = policy.staff_scope(db, actor, user_id, None)
    return people.matching_fields_view(db, actor.id, role, user_id, None)


@router.get("/access-log", response_model=list[AccessLogEntry], summary="Staff access log")
def access_log(actor: AdminActor, db: Db) -> list[AccessLogEntry]:
    return admin.access_log(db)


@router.post(
    "/venues",
    response_model=Venue,
    status_code=201,
    responses=error_responses(422),
    summary="Add a venue",
)
def create_venue(body: VenueWrite, actor: AdminActor, db: Db) -> Venue:
    return events.save_venue(db, None, body)


@router.put(
    "/venues/{venue_id}",
    response_model=Venue,
    responses=error_responses(404, 422),
    summary="Edit a venue",
)
def update_venue(venue_id: UUID, body: VenueWrite, actor: AdminActor, db: Db) -> Venue:
    return events.save_venue(db, venue_id, body)


@router.delete(
    "/venues/{venue_id}", status_code=204, responses=error_responses(404), summary="Remove a venue"
)
def delete_venue(venue_id: UUID, actor: AdminActor, db: Db) -> Response:
    events.delete_venue(db, venue_id)
    return Response(status_code=204)


@router.get("/metrics", response_model=Metrics, summary="Funnel and AI health (synthetic)")
def metrics(actor: AdminActor, db: Db) -> Metrics:
    return admin.metrics(db)
