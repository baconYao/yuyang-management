"""drop bill.monthly_rent

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-17

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("bill", "monthly_rent")


def downgrade() -> None:
    op.add_column(
        "bill",
        sa.Column(
            "monthly_rent",
            sa.DOUBLE_PRECISION(),
            nullable=False,
            server_default="0",
        ),
    )
