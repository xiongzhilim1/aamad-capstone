"""Synthetic persona login (US-001)."""

from uuid import UUID

from pydantic import Field

from app.api.schemas.common import ApiModel
from app.domain.vocab import Role, Stage


class DemoAccessRequest(ApiModel):
    access_code: str = Field(min_length=1, max_length=200)


class PersonaOption(ApiModel):
    id: UUID
    display_name: str
    stage: Stage
    roles: list[Role]
    blurb: str = Field(description="One line on what this persona is useful for in the demo.")


class PersonaLoginRequest(ApiModel):
    persona_id: UUID


class CurrentUser(ApiModel):
    id: UUID
    display_name: str
    stage: Stage
    roles: list[Role] = Field(
        description="`facilitator` is present when the user facilitates at least one circle."
    )
    onboarding_completed: bool
    synthetic: bool = True


class SessionState(ApiModel):
    demo_access: bool = Field(description="True once the demo access code has been accepted.")
    user: CurrentUser | None = None
