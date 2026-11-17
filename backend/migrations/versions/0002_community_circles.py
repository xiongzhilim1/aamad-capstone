"""community circles

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "circles",
        sa.Column("community_tagged", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column("circles", sa.Column("community_label", sa.String(length=40), nullable=True))


def downgrade() -> None:
    op.drop_column("circles", "community_label")
    op.drop_column("circles", "community_tagged")
