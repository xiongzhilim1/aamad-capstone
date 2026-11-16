"""Events, registration, attendance, reconnection (US-004, US-012-015, US-018-020, US-025)."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.api.deps import CurrentActor
from app.api.errors import error_responses
from app.api.schemas.events import (
    AttendanceMark,
    AttendanceResult,
    CheckinCodeIssued,
    CheckinRequest,
    EventCard,
    EventDetail,
    EventWrite,
    HostAttendance,
    ReconnectConsentUpdate,
    ReconnectList,
    RegistrationResult,
    Venue,
)
from app.db.session import Db
from app.services import events, policy

router = APIRouter(tags=["events"], responses=error_responses(401))

_NOT_VISIBLE = error_responses(404)
_HOST = error_responses(403, 404)


@router.get("/events", response_model=list[EventCard], summary="Published events")
def list_events(
    actor: CurrentActor,
    db: Db,
    when: Annotated[Literal["upcoming", "past", "all"], Query()] = "all",
) -> list[EventCard]:
    """Approved events only (MN-005)."""
    return events.list_published(db, actor, when)


@router.get("/events/mine", response_model=list[EventCard], summary="Events I organise or co-host")
def list_my_events(actor: CurrentActor, db: Db) -> list[EventCard]:
    """Every state, including drafts and rejected events."""
    return events.list_mine(db, actor)


@router.post(
    "/events",
    response_model=EventDetail,
    status_code=201,
    responses=error_responses(403, 404, 422),
    summary="Create a draft event (organiser)",
)
def create_event(body: EventWrite, actor: CurrentActor, db: Db) -> EventDetail:
    return events.create(db, actor, body)


@router.get(
    "/events/{event_id}", response_model=EventDetail, responses=_NOT_VISIBLE, summary="An event"
)
def get_event(event_id: UUID, actor: CurrentActor, db: Db) -> EventDetail:
    """An unapproved event is 404 to everyone but its organiser, co-hosts and the admin (AC-006)."""
    return events.detail(db, policy.visible_event(db, event_id, actor), actor)


@router.put(
    "/events/{event_id}",
    response_model=EventDetail,
    responses=error_responses(403, 404, 409, 422),
    summary="Edit a draft (organiser or co-host)",
)
def update_event(event_id: UUID, body: EventWrite, actor: CurrentActor, db: Db) -> EventDetail:
    """Drafts and rejected events only; withdraw a submission first (`409 not_editable`)."""
    return events.update(db, actor, event_id, body)


@router.post(
    "/events/{event_id}/submit",
    response_model=EventDetail,
    responses=error_responses(403, 404, 409),
    summary="Submit for admin approval (organiser)",
)
def submit_event(event_id: UUID, actor: CurrentActor, db: Db) -> EventDetail:
    return events.submit(db, actor, event_id)


@router.post(
    "/events/{event_id}/withdraw",
    response_model=EventDetail,
    responses=error_responses(403, 404, 409),
    summary="Withdraw a submission back to draft (organiser)",
)
def withdraw_event(event_id: UUID, actor: CurrentActor, db: Db) -> EventDetail:
    return events.withdraw_submission(db, actor, event_id)


@router.post(
    "/events/{event_id}/cancel",
    response_model=EventDetail,
    responses=error_responses(403, 404, 409),
    summary="Cancel an approved event (organiser or admin)",
)
def cancel_event(event_id: UUID, actor: CurrentActor, db: Db) -> EventDetail:
    return events.cancel(db, actor, event_id)


@router.put(
    "/events/{event_id}/co-hosts/{user_id}",
    response_model=EventDetail,
    responses=_HOST,
    summary="Assign a co-host (organiser)",
)
def add_co_host(event_id: UUID, user_id: UUID, actor: CurrentActor, db: Db) -> EventDetail:
    return events.set_co_host(db, actor, event_id, user_id, add=True)


@router.delete(
    "/events/{event_id}/co-hosts/{user_id}",
    response_model=EventDetail,
    responses=_HOST,
    summary="Remove a co-host (organiser)",
)
def remove_co_host(event_id: UUID, user_id: UUID, actor: CurrentActor, db: Db) -> EventDetail:
    return events.set_co_host(db, actor, event_id, user_id, add=False)


@router.post(
    "/events/{event_id}/registrations",
    response_model=RegistrationResult,
    responses=error_responses(404, 409),
    summary="Register",
)
def register(event_id: UUID, actor: CurrentActor, db: Db) -> RegistrationResult:
    """Approved events only. Changes no consent and no membership (MN-001, MN-007)."""
    return events.register(db, actor, event_id)


@router.delete(
    "/events/{event_id}/registrations/me",
    response_model=RegistrationResult,
    responses=_NOT_VISIBLE,
    summary="Withdraw my registration",
)
def unregister(event_id: UUID, actor: CurrentActor, db: Db) -> RegistrationResult:
    return events.unregister(db, actor, event_id)


@router.get(
    "/events/{event_id}/attendance",
    response_model=HostAttendance,
    responses=_HOST,
    summary="Host tools: attendance lists",
)
def get_attendance(event_id: UUID, actor: CurrentActor, db: Db) -> HostAttendance:
    return events.host_attendance(db, actor, event_id)


@router.put(
    "/events/{event_id}/attendance",
    response_model=HostAttendance,
    responses=error_responses(403, 404, 409, 422),
    summary="Mark or unmark attendance (organiser or co-host)",
)
def mark_attendance(
    event_id: UUID, body: AttendanceMark, actor: CurrentActor, db: Db
) -> HostAttendance:
    """Only after the event starts (`409 event_not_started`). `attended: false` also removes
    someone who joined by code. Corrections are recorded (US-015)."""
    return events.mark(db, actor, event_id, body.user_id, body.attended)


@router.post(
    "/events/{event_id}/attendance-claims",
    response_model=AttendanceResult,
    status_code=201,
    responses=error_responses(404, 409),
    summary='"I was there": ask the host to confirm',
)
def claim_attendance(event_id: UUID, actor: CurrentActor, db: Db) -> AttendanceResult:
    """Approved, started events only; no registration needed (MD-023). Reveals nothing (MN-017)."""
    return events.claim(db, actor, event_id)


@router.delete(
    "/events/{event_id}/attendance-claims/me",
    response_model=AttendanceResult,
    responses=_NOT_VISIBLE,
    summary="Withdraw my claim",
)
def withdraw_claim(event_id: UUID, actor: CurrentActor, db: Db) -> AttendanceResult:
    return events.withdraw_claim(db, actor, event_id)


@router.post(
    "/events/{event_id}/attendance-claims/{claim_id}/approve",
    response_model=HostAttendance,
    responses=_HOST,
    summary="Approve a claim (organiser or co-host)",
)
def approve_claim(event_id: UUID, claim_id: UUID, actor: CurrentActor, db: Db) -> HostAttendance:
    return events.decide_claim(db, actor, event_id, claim_id, approve=True)


@router.post(
    "/events/{event_id}/attendance-claims/{claim_id}/decline",
    response_model=HostAttendance,
    responses=_HOST,
    summary="Decline a claim (organiser or co-host)",
)
def decline_claim(event_id: UUID, claim_id: UUID, actor: CurrentActor, db: Db) -> HostAttendance:
    return events.decide_claim(db, actor, event_id, claim_id, approve=False)


@router.post(
    "/events/{event_id}/checkin",
    response_model=AttendanceResult,
    responses=error_responses(404, 422, 429),
    summary="Enter the event code",
)
def checkin(event_id: UUID, body: CheckinRequest, actor: CurrentActor, db: Db) -> AttendanceResult:
    """A valid code within 7 days of the event's end confirms attendance at once (MD-024).

    `422 code_invalid` or `422 code_expired` change nothing. The sixth wrong attempt in an
    hour is `429 rate_limited` with `retry_at` (AC-022).
    """
    return events.checkin(db, actor, event_id, body.code)


@router.put(
    "/events/{event_id}/checkin-code",
    response_model=CheckinCodeIssued,
    responses=error_responses(403, 404, 409),
    summary="Generate or rotate the event code (organiser or co-host)",
)
def rotate_checkin_code(event_id: UUID, actor: CurrentActor, db: Db) -> CheckinCodeIssued:
    """Returns the new code once. The previous code stops working."""
    return events.rotate_code(db, actor, event_id)


@router.delete(
    "/events/{event_id}/checkin-code",
    status_code=204,
    responses=_HOST,
    summary="Turn the event code off (organiser or co-host)",
)
def disable_checkin_code(event_id: UUID, actor: CurrentActor, db: Db) -> Response:
    events.disable_code(db, actor, event_id)
    return Response(status_code=204)


@router.put(
    "/events/{event_id}/reconnect-consent",
    response_model=EventDetail,
    responses=error_responses(403, 404, 409, 422),
    summary="Opt in or out of this event's reconnection list",
)
def put_reconnect_consent(
    event_id: UUID, body: ReconnectConsentUpdate, actor: CurrentActor, db: Db
) -> EventDetail:
    """Needs confirmed attendance (`403 attendance_not_confirmed`) and an ended event
    (`409 event_not_ended`). Never changes directory consent (MN-001)."""
    return events.set_reconnect_consent(db, actor, event_id, body.opted_in)


@router.get(
    "/events/{event_id}/reconnect",
    response_model=ReconnectList,
    responses=error_responses(403, 404, 409),
    summary="People from this event who opted in",
)
def get_reconnect_list(event_id: UUID, actor: CurrentActor, db: Db) -> ReconnectList:
    """Only for viewers with confirmed attendance who opted in (`403 attendance_not_confirmed`,
    `403 reconnect_not_opted_in`). A claimed or declined person sees no attendee data (CR-017)."""
    return events.reconnect_list(db, actor, event_id)


@router.get("/venues", response_model=list[Venue], summary="Curated venue directory")
def list_venues(actor: CurrentActor, db: Db) -> list[Venue]:
    return events.list_venues(db)
