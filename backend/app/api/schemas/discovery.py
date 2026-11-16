"""Directory, filter discovery and AI suggestions (US-003, US-005, US-006)."""

from typing import Literal

from pydantic import Field

from app.api.schemas.common import AiFallback, ApiModel, CircleCard, DiscoverResults, PersonCard


class DirectoryResponse(ApiModel):
    people: list[PersonCard]


class SuggestionItem(ApiModel):
    """One AI suggestion. Exactly one of `person` or `circle` is set, matching `kind`."""

    kind: Literal["person", "circle"]
    reason: str = Field(description="At most 25 words; cites only fields shown on the card.")
    cited_fields: list[str] = Field(
        description="Profile field names the reason relies on, e.g. `interests`, `stage`."
    )
    person: PersonCard | None = None
    circle: CircleCard | None = None


class SuggestionsResponse(ApiModel):
    """`ok`: AI suggestions (label them "Suggested by AI").

    `fallback`: the AI path did not produce a list; `filter_results` holds unfiltered
    discovery results so the page is never empty (MC-005, AC-009).
    """

    status: Literal["ok", "fallback"]
    items: list[SuggestionItem] = Field(default=[], max_length=10)
    fallback: AiFallback | None = None
    filter_results: DiscoverResults | None = None
    trace_id: str
