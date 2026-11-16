"""Directory, filter discovery and AI suggestions (US-003, US-005, US-006)."""

from typing import Annotated

from fastapi import APIRouter, Query, Request

from app.ai import suggestions
from app.api.deps import CurrentActor
from app.api.errors import error_responses, trace_id_of
from app.api.schemas.common import DiscoverResults
from app.api.schemas.discovery import DirectoryResponse, SuggestionsResponse
from app.db.session import Db
from app.domain.vocab import Area, Challenge, Interest, MeetingMode, Stage
from app.services import discovery

router = APIRouter(tags=["discovery"], responses=error_responses(401))


@router.get("/directory", response_model=DirectoryResponse, summary="Opt-in people directory")
def get_directory(actor: CurrentActor, db: Db) -> DirectoryResponse:
    """Only people who opted in, minus me and anyone blocked either way (AC-001, AC-005)."""
    return DirectoryResponse(people=discovery.directory(db, actor))


@router.get(
    "/discover",
    response_model=DiscoverResults,
    responses=error_responses(422),
    summary="Filter people and circles",
)
def discover(
    actor: CurrentActor,
    db: Db,
    stage: Annotated[list[Stage] | None, Query(description="Any of these stages.")] = None,
    interests: Annotated[list[Interest] | None, Query(description="Has all of these.")] = None,
    challenges: Annotated[list[Challenge] | None, Query(description="Has all of these.")] = None,
    area: Annotated[Area | None, Query()] = None,
    meeting_mode: Annotated[MeetingMode | None, Query()] = None,
    circle_faith_tagged: Annotated[
        bool | None, Query(description="Circles only. There is no faith filter on people.")
    ] = None,
) -> DiscoverResults:
    """Results match every applied filter (MD-004). Filters see public fields only (MD-020).

    Works when the AI is unavailable (MC-005).
    """
    return discovery.discover(
        db,
        actor,
        stage=[s.value for s in stage] if stage else None,
        interests=[i.value for i in interests] if interests else None,
        challenges=[c.value for c in challenges] if challenges else None,
        area=area.value if area else None,
        meeting_mode=meeting_mode.value if meeting_mode else None,
        circle_faith_tagged=circle_faith_tagged,
    )


@router.post("/suggestions", response_model=SuggestionsResponse, summary="Suggest for me")
def suggest(request: Request, actor: CurrentActor, db: Db) -> SuggestionsResponse:
    """Runs the suggestion crew once, on demand (W06 to W08, MC-001). Changes no state (MN-003).

    Always HTTP 200: `status: fallback` carries the reason and unfiltered discovery results.
    Limited to 10 per hour per user (CR-010).
    """
    return suggestions.suggest(db, actor, trace_id_of(request))
