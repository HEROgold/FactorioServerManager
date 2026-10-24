"""Create the users table.

Revision ID: 0001
Revises:
Create Date: 2026-10-24
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Apply this revision."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("password", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("_display_name", sa.String(), nullable=True),
    )


def downgrade() -> None:
    """Revert this revision."""
    op.drop_table("users")
