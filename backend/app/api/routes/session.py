"""Session: demo access code, then a synthetic persona (US-001, SAD §8 AuthN)."""

import threading
import time
from datetime import UTC, datetime

from fastapi import APIRouter, Request, Response
from sqlalchemy import select

from app.ai import profile_assistant
from app.api.deps import CurrentActor, DemoSession, read_session
from app.api.errors import ApiError, error_responses, forbidden, not_found
from app.api.schemas.profile import Vocabulary
from app.api.schemas.session import (
    CurrentUser,
    DemoAccessRequest,
    PersonaLoginRequest,
    PersonaOption,
    SessionState,
)
from app.db.models import Profile, User
from app.db.session import Db
from app.security import SessionData, demo_code_matches, new_session_data, set_session_cookie
from app.services import admin as admin_service
from app.services import people

router = APIRouter(tags=["session"])

MAX_WRONG_ACCESS_CODES = 10


class _AccessAttempts:
    """Wrong demo codes per client address: 10 per hour, held in memory (SAD §8)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._failures: dict[str, list[float]] = {}

    def blocked_until(self, client: str) -> datetime | None:
        with self._lock:
            recent = [t for t in self._failures.get(client, []) if t > time.time() - 3600]
            self._failures[client] = recent
            if len(recent) < MAX_WRONG_ACCESS_CODES:
                return None
            return datetime.fromtimestamp(recent[0] + 3600, UTC)

    def record(self, client: str) -> None:
        with self._lock:
            self._failures.setdefault(client, []).append(time.time())

    def reset(self) -> None:
        with self._lock:
            self._failures.clear()


_attempts = _AccessAttempts()


def _state(db: Db, data: SessionData | None) -> SessionState:
    if data is None or not data.demo:
        return SessionState(demo_access=False, user=None)
    user = db.get(User, data.user_id) if data.user_id else None
    profile = db.get(Profile, user.id) if user else None
    if user is None or profile is None:
        return SessionState(demo_access=True, user=None)
    return SessionState(
        demo_access=True,
        user=CurrentUser(
            id=user.id,
            display_name=user.display_name,
            stage=profile.stage,
            roles=admin_service.roles_of(db, user),
            onboarding_completed=profile.onboarding_completed,
            synthetic=user.synthetic,
        ),
    )


@router.post(
    "/session/demo-access",
    response_model=SessionState,
    responses=error_responses(403, 422, 429),
    summary="Enter the demo access code",
)
def enter_demo_access(
    body: DemoAccessRequest, request: Request, response: Response, db: Db
) -> SessionState:
    """Sets the session cookie with demo access. Wrong codes are rate limited."""
    client = request.client.host if request.client else "unknown"
    retry_at = _attempts.blocked_until(client)
    if retry_at is not None:
        raise ApiError(429, "rate_limited", "Too many tries. Try again later.", retry_at=retry_at)
    if not demo_code_matches(body.access_code):
        _attempts.record(client)
        raise forbidden("That access code didn't work.", "access_code_invalid")
    data = read_session(request) or new_session_data()
    set_session_cookie(response, data)
    return _state(db, data)


@router.get("/session", response_model=SessionState, summary="Current session")
def get_session(request: Request, db: Db) -> SessionState:
    """Never fails: returns `demo_access: false` and `user: null` when there is no session."""
    return _state(db, read_session(request))


@router.get(
    "/session/personas",
    response_model=list[PersonaOption],
    responses=error_responses(403),
    summary="List seeded personas for the picker",
)
def list_personas(session: DemoSession, db: Db) -> list[PersonaOption]:
    """Requires demo access. All personas are synthetic (MN-008)."""
    rows = db.execute(
        select(User, Profile).join(Profile, Profile.user_id == User.id).order_by(User.display_name)
    ).all()
    return [
        PersonaOption(
            id=u.id,
            display_name=u.display_name,
            stage=p.stage,
            roles=admin_service.roles_of(db, u),
            blurb=u.persona_blurb,
        )
        for u, p in rows
    ]


@router.post(
    "/session/persona",
    response_model=SessionState,
    responses=error_responses(403, 404, 422),
    summary="Sign in as a persona",
)
def choose_persona(
    body: PersonaLoginRequest, session: DemoSession, response: Response, db: Db
) -> SessionState:
    """Requires demo access. Every later request acts as this persona (MN-011)."""
    if db.get(User, body.persona_id) is None:
        raise not_found("We couldn't find that persona.")
    # A fresh session id per sign-in, so nothing held for the previous persona carries over.
    profile_assistant.store.pop(session.sid)
    data = new_session_data().with_user(body.persona_id)
    set_session_cookie(response, data)
    return _state(db, data)


@router.delete("/session", status_code=204, summary="Sign out")
def end_session(request: Request, response: Response) -> Response:
    """Ends the persona session and discards any unsaved assistant draft. Demo access is kept."""
    data = read_session(request)
    if data is not None:
        profile_assistant.store.pop(data.sid)  # unsaved raw text is deleted (MN-015)
        set_session_cookie(response, new_session_data() if data.demo else data.with_user(None))
    response.status_code = 204
    return response


@router.get(
    "/vocabulary",
    response_model=Vocabulary,
    responses=error_responses(401),
    summary="Tag lists for the pickers",
)
def get_vocabulary(actor: CurrentActor) -> Vocabulary:
    return people.vocabulary()
