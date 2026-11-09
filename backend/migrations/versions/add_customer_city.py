"""Add customer.city (NOT NULL).

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-11-08

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # server_default "" backfills existing rows; city must never be NULL
    op.add_column(
        "customer",
        sa.Column("city", sa.String(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("customer", "city")
