"""Request dependencies: the actor always comes from the session cookie (MN-011, CR-011)."""

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import APIKeyCookie

from app.api.errors import ApiError, forbidden
from app.db.models import User
from app.db.session import Db
from app.security import SESSION_COOKIE, SessionData, decode_session

# Declared so the OpenAPI document shows cookie auth; the cookie is HttpOnly and set by the server.
_cookie_scheme = APIKeyCookie(
    name=SESSION_COOKIE,
    auto_error=False,
    description="HttpOnly session cookie set by `POST /session/persona`.",
)


@dataclass(frozen=True)
class Actor:
    """The authenticated user for this request. Built only from the session, never from input."""

    id: UUID
    session_id: str
    is_admin: bool
    is_organiser: bool
    display_name: str


def read_session(request: Request) -> SessionData | None:
    return decode_session(request.cookies.get(SESSION_COOKIE))


def require_demo(request: Request) -> SessionData:
    data = read_session(request)
    if data is None or not data.demo:
        raise forbidden("Enter the demo access code first.", "demo_access_required")
    return data


def get_actor(
    request: Request, db: Db, _cookie: Annotated[str | None, Depends(_cookie_scheme)]
) -> Actor:
    data = read_session(request)
    user = db.get(User, data.user_id) if data and data.demo and data.user_id else None
    if data is None or user is None:
        raise ApiError(401, "not_signed_in", "Choose a persona to continue.")
    return Actor(user.id, data.sid, user.is_admin, user.is_organiser, user.display_name)


def get_admin(actor: Annotated[Actor, Depends(get_actor)]) -> Actor:
    if not actor.is_admin:
        raise forbidden("Only the admin can do that.")
    return actor


CurrentActor = Annotated[Actor, Depends(get_actor)]
AdminActor = Annotated[Actor, Depends(get_admin)]
DemoSession = Annotated[SessionData, Depends(require_demo)]
