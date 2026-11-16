"""initial schema

Revision ID: 0001
Revises:
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

TABLES = (
    "circles",
    "users",
    "venues",
    "blocks",
    "circle_facilitators",
    "circle_memberships",
    "connection_requests",
    "events",
    "model_traces",
    "profile_fields",
    "profiles",
    "reports",
    "staff_access_log",
    "attendance",
    "attendance_log",
    "checkin_attempts",
    "connections",
    "discovery_consents",
    "event_approvals",
    "event_checkin_codes",
    "event_hosts",
    "registrations",
    "contact_shares",
    "follow_up_reports",
)


def upgrade() -> None:
    op.create_table(
        "circles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("purpose", sa.String(length=400), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("admission_policy", sa.String(length=12), nullable=False),
        sa.Column("member_list_visibility", sa.String(length=12), nullable=False),
        sa.Column("meeting_mode", sa.String(length=12), nullable=True),
        sa.Column("area", sa.String(length=24), nullable=True),
        sa.Column("faith_tagged", sa.Boolean(), nullable=False),
        sa.Column("faith_context_label", sa.String(length=40), nullable=True),
        sa.Column("synthetic", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=60), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("is_organiser", sa.Boolean(), nullable=False),
        sa.Column("persona_blurb", sa.String(length=200), nullable=False),
        sa.Column("synthetic", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "venues",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("area", sa.String(length=200), nullable=True),
        sa.Column("address_hint", sa.String(length=200), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(length=200), nullable=True),
        sa.Column("synthetic", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "blocks",
        sa.Column("blocker_id", sa.Uuid(), nullable=False),
        sa.Column("blocked_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["blocked_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["blocker_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("blocker_id", "blocked_id"),
    )
    op.create_table(
        "circle_facilitators",
        sa.Column("circle_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["circle_id"], ["circles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("circle_id", "user_id"),
    )
    op.create_table(
        "circle_memberships",
        sa.Column("circle_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("status in ('member','applicant')", name="status_valid"),
        sa.ForeignKeyConstraint(["circle_id"], ["circles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("circle_id", "user_id"),
    )
    op.create_table(
        "connection_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("sender_id", sa.Uuid(), nullable=False),
        sa.Column("recipient_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False),
        sa.Column("sender_hidden", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status in ('pending','accepted','declined','withdrawn')", name="status_valid"
        ),
        sa.CheckConstraint("sender_id <> recipient_id", name="not_self"),
        sa.ForeignKeyConstraint(["recipient_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_request_open",
        "connection_requests",
        ["sender_id", "recipient_id"],
        unique=True,
        postgresql_where=sa.text("status in ('pending','declined')"),
    )
    op.create_table(
        "events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organiser_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("mode", sa.String(length=12), nullable=False),
        sa.Column("venue_id", sa.Uuid(), nullable=True),
        sa.Column("venue_text", sa.String(length=200), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("price_amount", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("price_currency", sa.String(length=3), nullable=True),
        sa.Column("includes", sa.String(length=200), nullable=True),
        sa.Column("circle_id", sa.Uuid(), nullable=True),
        sa.Column("state", sa.String(length=12), nullable=False),
        sa.Column("added_after_event", sa.Boolean(), nullable=False),
        sa.Column("synthetic", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "state in ('draft','submitted','approved','rejected','cancelled')", name="state_valid"
        ),
        sa.CheckConstraint("ends_at > starts_at", name="ends_after_start"),
        sa.ForeignKeyConstraint(["circle_id"], ["circles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organiser_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["venue_id"], ["venues.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "model_traces",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("trace_id", sa.String(length=32), nullable=False),
        sa.Column("crew", sa.String(length=24), nullable=False),
        sa.Column("task_id", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=48), nullable=False),
        sa.Column("effort", sa.String(length=8), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("outcome", sa.String(length=12), nullable=False),
        sa.Column("fallback_code", sa.String(length=24), nullable=True),
        sa.Column("input_ids", sa.JSON(), nullable=False),
        sa.Column("output_ids", sa.JSON(), nullable=False),
        sa.Column("dropped", sa.JSON(), nullable=False),
        sa.Column("model_calls", sa.Integer(), nullable=False),
        sa.Column("schema_failures", sa.Integer(), nullable=False),
        sa.Column("stop_reason", sa.String(length=24), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("review_outcome", sa.String(length=12), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_model_traces_trace_id"), "model_traces", ["trace_id"], unique=False)
    op.create_index(
        "ix_traces_user_crew_time", "model_traces", ["user_id", "crew", "created_at"], unique=False
    )
    op.create_table(
        "profile_fields",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("field", sa.String(length=24), nullable=False),
        sa.Column("value", sa.JSON(), nullable=False),
        sa.Column("visibility", sa.String(length=16), nullable=False),
        sa.CheckConstraint("visibility in ('public','matching_only')", name="visibility_valid"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "field"),
    )
    op.create_table(
        "profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.String(length=16), nullable=False),
        sa.Column("faith_matching_opt_in", sa.Boolean(), nullable=False),
        sa.Column("onboarding_completed", sa.Boolean(), nullable=False),
        sa.Column("contact_email", sa.String(length=120), nullable=True),
        sa.Column("contact_phone", sa.String(length=120), nullable=True),
        sa.Column("contact_other", sa.String(length=120), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("stage in ('seasoned','new','aspiring')", name="stage_valid"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("reporter_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["subject_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "staff_access_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("viewer_id", sa.Uuid(), nullable=False),
        sa.Column("viewer_role", sa.String(length=12), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("fields", sa.JSON(), nullable=False),
        sa.Column("circle_id", sa.Uuid(), nullable=True),
        sa.Column(
            "viewed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.ForeignKeyConstraint(["circle_id"], ["circles.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["subject_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["viewer_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "attendance",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False),
        sa.Column("source", sa.String(length=12), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("source in ('organiser','claim','code')", name="source_valid"),
        sa.CheckConstraint("status in ('claimed','confirmed','declined')", name="status_valid"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", "user_id"),
    )
    op.create_table(
        "attendance_log",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("from_status", sa.String(length=12), nullable=False),
        sa.Column("to_status", sa.String(length=12), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "checkin_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("succeeded", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_a", sa.Uuid(), nullable=False),
        sa.Column("user_b", sa.Uuid(), nullable=False),
        sa.Column("request_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("user_a < user_b", name="ordered_pair"),
        sa.ForeignKeyConstraint(["request_id"], ["connection_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_a"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_b"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_a", "user_b"),
    )
    op.create_table(
        "discovery_consents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uq_consent_event",
        "discovery_consents",
        ["user_id", "event_id"],
        unique=True,
        postgresql_where=sa.text("event_id is not null"),
    )
    op.create_index(
        "uq_consent_global",
        "discovery_consents",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("event_id is null"),
    )
    op.create_table(
        "event_approvals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("admin_id", sa.Uuid(), nullable=False),
        sa.Column("decision", sa.String(length=8), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column(
            "decided_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["admin_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "event_checkin_codes",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column(
            "rotated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_table(
        "event_hosts",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("event_id", "user_id"),
    )
    op.create_table(
        "registrations",
        sa.Column("event_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("event_id", "user_id"),
    )
    op.create_table(
        "contact_shares",
        sa.Column("connection_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["connection_id"], ["connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("connection_id", "user_id"),
    )
    op.create_table(
        "follow_up_reports",
        sa.Column("connection_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("reporter_id", sa.Uuid(), nullable=False),
        sa.Column("met", sa.Boolean(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=True),
        sa.Column("period_end", sa.Date(), nullable=True),
        sa.Column("usefulness", sa.Integer(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("number in (1, 2)", name="number_valid"),
        sa.ForeignKeyConstraint(["connection_id"], ["connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("connection_id", "number", "reporter_id"),
    )

    # SAD §4, §8: Row Level Security is enabled with no policies on every table, so the
    # Supabase anon and authenticated roles can read nothing. The backend connects as the
    # table owner, which RLS does not restrict.
    for table in TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')


def downgrade() -> None:
    op.drop_table("follow_up_reports")
    op.drop_table("contact_shares")
    op.drop_table("registrations")
    op.drop_table("event_hosts")
    op.drop_table("event_checkin_codes")
    op.drop_table("event_approvals")
    op.drop_index(
        "uq_consent_global",
        table_name="discovery_consents",
        postgresql_where=sa.text("event_id is null"),
    )
    op.drop_index(
        "uq_consent_event",
        table_name="discovery_consents",
        postgresql_where=sa.text("event_id is not null"),
    )
    op.drop_table("discovery_consents")
    op.drop_table("connections")
    op.drop_table("checkin_attempts")
    op.drop_table("attendance_log")
    op.drop_table("attendance")
    op.drop_table("staff_access_log")
    op.drop_table("reports")
    op.drop_table("profiles")
    op.drop_table("profile_fields")
    op.drop_index("ix_traces_user_crew_time", table_name="model_traces")
    op.drop_index(op.f("ix_model_traces_trace_id"), table_name="model_traces")
    op.drop_table("model_traces")
    op.drop_table("events")
    op.drop_index(
        "uq_request_open",
        table_name="connection_requests",
        postgresql_where=sa.text("status in ('pending','declined')"),
    )
    op.drop_table("connection_requests")
    op.drop_table("circle_memberships")
    op.drop_table("circle_facilitators")
    op.drop_table("blocks")
    op.drop_table("venues")
    op.drop_table("users")
    op.drop_table("circles")
