"""make bill.due_date nullable

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-01-31

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f5a6b7c8d9e0"
down_revision: str | Sequence[str] | None = "e4f5a6b7c8d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "bill",
        "due_date",
        existing_type=sa.TIMESTAMP(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "bill",
        "due_date",
        existing_type=sa.TIMESTAMP(),
        nullable=False,
    )
