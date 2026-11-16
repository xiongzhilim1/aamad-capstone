"""Admin views: reports, roles, staff access log, funnel metrics (US-010, US-013, US-022)."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.api.schemas.common import ApiModel, PersonRef
from app.domain.vocab import ProfileField, Role, Stage


class Report(ApiModel):
    """Visible to the admin only (NFR-008)."""

    id: UUID
    reporter: PersonRef
    subject: PersonRef
    reason: str
    created_at: datetime


class AdminUser(ApiModel):
    id: UUID
    display_name: str
    stage: Stage
    roles: list[Role]


class RoleUpdate(ApiModel):
    organiser: bool = Field(description="Grant or remove the organiser role.")


class AccessLogEntry(ApiModel):
    """One staff view of `matching_only` fields (CR-016)."""

    id: UUID
    viewer: PersonRef
    viewer_role: Role
    subject: PersonRef
    fields: list[ProfileField]
    circle_id: UUID | None = None
    viewed_at: datetime


class FunnelUnit(ApiModel):
    """One funnel unit: a count with its own denominator. Never combined (MD-016)."""

    key: str
    label: str
    count: int
    denominator: int
    denominator_label: str
    self_reported: bool = False


class AiHealth(ApiModel):
    """Aggregate view built from model traces; never shows profile content (Production Shape)."""

    spend_usd: float
    spend_cap_usd: float
    ai_enabled: bool
    calls: int
    fallback_rate: float | None
    schema_failure_rate: float | None
    dropped_item_rate: float | None
    p95_latency_ms: int | None
    assistant_accepted: int
    assistant_discarded: int


class Metrics(ApiModel):
    synthetic: bool = Field(default=True, description="All figures are synthetic (NFR-009).")
    funnel: list[FunnelUnit]
    ai: AiHealth
    generated_at: datetime
