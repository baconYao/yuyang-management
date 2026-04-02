"""Migrate contract status TRIAL to PENDING (TRIAL removed from app).

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-02-19

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE contract SET status = 'PENDING' WHERE status = 'TRIAL'")


def downgrade() -> None:
    # Application no longer supports TRIAL; no-op.
    pass
