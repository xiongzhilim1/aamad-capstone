"""Requests, connections, contact sharing, blocks, reports, follow-ups (US-007-010, US-021)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Response

from app.api.deps import CurrentActor
from app.api.errors import error_responses
from app.api.schemas.connections import (
    Block,
    BlockCreate,
    Connection,
    ConnectionRequest,
    ContactShareUpdate,
    FollowUpReport,
    ReportCreate,
    ReportReceipt,
    RequestCreate,
    RequestInbox,
)
from app.db.session import Db
from app.services import connections, policy

router = APIRouter(tags=["connections"], responses=error_responses(401))


@router.get("/requests", response_model=RequestInbox, summary="My pending requests")
def list_requests(actor: CurrentActor, db: Db) -> RequestInbox:
    return connections.inbox(db, actor)


@router.post(
    "/requests",
    response_model=ConnectionRequest,
    status_code=201,
    responses=error_responses(404, 409, 422),
    summary="Ask to connect",
)
def send_request(body: RequestCreate, actor: CurrentActor, db: Db) -> ConnectionRequest:
    """The recipient must be visible to me (directory, filters, suggestions or a reconnection list).

    Idempotent: repeating it returns the same pending request. `409 request_already_received`
    when they already asked me (never auto-accepts). `409 already_connected`. A blocked pair
    gets `404` (AC-005).
    """
    return connections.send(db, actor, body.recipient_id)


@router.delete(
    "/requests/{request_id}",
    status_code=204,
    responses=error_responses(404),
    summary="Withdraw my request",
)
def withdraw_request(request_id: UUID, actor: CurrentActor, db: Db) -> Response:
    connections.withdraw(db, actor, request_id)
    return Response(status_code=204)


@router.post(
    "/requests/{request_id}/accept",
    response_model=Connection,
    responses=error_responses(403, 404),
    summary="Accept a request",
)
def accept_request(request_id: UUID, actor: CurrentActor, db: Db) -> Connection:
    """Recipient only: the sender gets 403, others 404 (AC-003). Shares no contacts (MN-002)."""
    return connections.accept(db, actor, request_id)


@router.post(
    "/requests/{request_id}/decline",
    status_code=204,
    responses=error_responses(403, 404),
    summary="Decline a request",
)
def decline_request(request_id: UUID, actor: CurrentActor, db: Db) -> Response:
    """Recipient only. Private: the sender is not told."""
    connections.decline(db, actor, request_id)
    return Response(status_code=204)


@router.get("/connections", response_model=list[Connection], summary="My connections")
def list_connections(actor: CurrentActor, db: Db) -> list[Connection]:
    return connections.list_connections(db, actor)


@router.get(
    "/connections/{connection_id}",
    response_model=Connection,
    responses=error_responses(404),
    summary="One connection",
)
def get_connection(connection_id: UUID, actor: CurrentActor, db: Db) -> Connection:
    """Members of the pair only; everyone else gets 404 (MN-006, AC-010)."""
    conn = policy.connection_for_member(db, connection_id, actor.id)
    return connections.connection_out(db, conn, actor.id)


@router.put(
    "/contact-shares/{connection_id}",
    response_model=Connection,
    responses=error_responses(404, 422),
    summary="Share or stop sharing my contact details",
)
def put_contact_share(
    connection_id: UUID, body: ContactShareUpdate, actor: CurrentActor, db: Db
) -> Connection:
    """Details show only while both sides share; revoking hides them at once (MD-007, AC-004)."""
    return connections.set_contact_share(db, actor, connection_id, body.share)


@router.put(
    "/connections/{connection_id}/follow-ups/{number}",
    response_model=Connection,
    responses=error_responses(404, 422),
    summary="Report a catch-up",
)
def put_follow_up(
    connection_id: UUID,
    number: Annotated[int, Path(ge=1, le=2, description="First (1) or second (2) catch-up.")],
    body: FollowUpReport,
    actor: CurrentActor,
    db: Db,
) -> Connection:
    """Idempotent self-report; a pair is counted once (MD-015, AC-013)."""
    return connections.report_follow_up(db, actor, connection_id, number, body)


@router.get("/blocks", response_model=list[Block], summary="People I blocked")
def list_blocks(actor: CurrentActor, db: Db) -> list[Block]:
    return connections.list_blocks(db, actor)


@router.post(
    "/blocks",
    response_model=Block,
    status_code=201,
    responses=error_responses(404, 422),
    summary="Block someone",
)
def create_block(body: BlockCreate, actor: CurrentActor, db: Db) -> Block:
    """Hides each from the other everywhere and hides any contact share (MD-008). Idempotent."""
    return connections.block(db, actor, body.user_id)


@router.delete("/blocks/{user_id}", status_code=204, summary="Unblock")
def delete_block(user_id: UUID, actor: CurrentActor, db: Db) -> Response:
    connections.unblock(db, actor, user_id)
    return Response(status_code=204)


@router.post(
    "/reports",
    response_model=ReportReceipt,
    status_code=201,
    responses=error_responses(404, 422),
    summary="Report someone to the admin",
)
def create_report(body: ReportCreate, actor: CurrentActor, db: Db) -> ReportReceipt:
    return connections.report(db, actor, body.subject_id, body.reason)
