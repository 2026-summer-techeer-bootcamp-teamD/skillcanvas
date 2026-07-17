"""add used_mcps to skills

Revision ID: c4a7e91f2b6d
Revises: b2f1a9c7d3e4
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c4a7e91f2b6d"
down_revision: str | None = "b2f1a9c7d3e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "skills",
        sa.Column("used_mcps", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("skills", "used_mcps")
