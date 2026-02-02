"""add contract status enum values: TRIAL, ENDED

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-01-31

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c8d9e0f1a2b3"
down_revision: str | Sequence[str] | None = "b7c8d9e0f1a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TYPE contractstatus ADD VALUE IF NOT EXISTS 'TRIAL'")
    op.execute("ALTER TYPE contractstatus ADD VALUE IF NOT EXISTS 'ENDED'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; leave as-is.
    pass
