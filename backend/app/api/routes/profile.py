"""Own profile, directory consent and the AI profile assistant (US-002, US-003, US-023, US-024)."""

from fastapi import APIRouter, Request, Response
from sqlalchemy import select

from app.ai import profile_assistant
from app.api.deps import CurrentActor
from app.api.errors import error_responses, trace_id_of
from app.api.schemas.profile import (
    DirectoryConsentUpdate,
    DraftAccept,
    DraftRequest,
    DraftResponse,
    OwnProfile,
    ProfileUpdate,
)
from app.db.models import DiscoveryConsent
from app.db.session import Db
from app.services import people

router = APIRouter(prefix="/me", tags=["profile"], responses=error_responses(401))


@router.get("/profile", response_model=OwnProfile, summary="My profile")
def get_my_profile(actor: CurrentActor, db: Db) -> OwnProfile:
    return people.own_profile(db, actor.id)


@router.put(
    "/profile",
    response_model=OwnProfile,
    responses=error_responses(422),
    summary="Save my profile",
)
def put_my_profile(body: ProfileUpdate, actor: CurrentActor, db: Db) -> OwnProfile:
    """Replaces the editable profile. Never changes discovery consent (MN-001)."""
    people.save_profile(db, actor.id, body, body.onboarding_completed)
    return people.own_profile(db, actor.id)


@router.put(
    "/directory-consent",
    response_model=OwnProfile,
    responses=error_responses(422),
    summary="List or unlist me in the directory",
)
def put_directory_consent(body: DirectoryConsentUpdate, actor: CurrentActor, db: Db) -> OwnProfile:
    """Global discovery consent (MD-002). Off by default; only this endpoint changes it."""
    row = db.scalar(
        select(DiscoveryConsent).where(
            DiscoveryConsent.user_id == actor.id, DiscoveryConsent.event_id.is_(None)
        )
    )
    if body.listed and row is None:
        db.add(DiscoveryConsent(user_id=actor.id, event_id=None))
    elif not body.listed and row is not None:
        db.delete(row)
    db.flush()
    return people.own_profile(db, actor.id)


@router.post(
    "/profile/draft",
    response_model=DraftResponse,
    responses=error_responses(422),
    summary="Summarise my own words into a draft",
)
def create_profile_draft(
    body: DraftRequest, request: Request, actor: CurrentActor, db: Db
) -> DraftResponse:
    """Runs the profile assistant once (W21). Nothing is saved (MN-013).

    Returns `status: fallback` (HTTP 200) when the assistant is unavailable, rate limited or
    over budget; the UI then offers the manual pickers (MC-006).
    """
    return profile_assistant.draft(db, actor, body.text, trace_id_of(request))


@router.get(
    "/profile/draft",
    response_model=DraftResponse,
    responses=error_responses(404),
    summary="My unsaved draft, if any",
)
def get_profile_draft(actor: CurrentActor) -> DraftResponse:
    return profile_assistant.current(actor)


@router.post(
    "/profile/draft/accept",
    response_model=OwnProfile,
    responses=error_responses(404, 422),
    summary="Save the fields I accepted",
)
def accept_profile_draft(body: DraftAccept, actor: CurrentActor, db: Db) -> OwnProfile:
    """Saves only the submitted fields with their visibility, then deletes the raw text (AC-017)."""
    profile_assistant.accept(db, actor, body)
    return people.own_profile(db, actor.id)


@router.delete("/profile/draft", status_code=204, summary="Discard my draft")
def discard_profile_draft(actor: CurrentActor, db: Db) -> Response:
    """Deletes the draft and the raw text (MN-015). Safe to call when no draft exists."""
    profile_assistant.discard(db, actor)
    return Response(status_code=204)
