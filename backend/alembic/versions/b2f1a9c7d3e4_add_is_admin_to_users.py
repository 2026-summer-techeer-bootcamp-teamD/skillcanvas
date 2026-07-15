"""add is_admin to users

Revision ID: b2f1a9c7d3e4
Revises: 5b5f2728ce43
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b2f1a9c7d3e4"
down_revision: str | None = "5b5f2728ce43"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("users", "is_admin")
