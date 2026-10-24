"""Store each user's encrypted Factorio token.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-24
"""

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Apply this revision."""
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("factorio_token", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    """Revert this revision."""
    with op.batch_alter_table("users") as batch:
        batch.drop_column("factorio_token")
