"""remove bill_id, add bill_number

Revision ID: d3e4f5a6b7c8
Revises: 811510926611
Create Date: 2025-01-31

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d3e4f5a6b7c8"
down_revision: str | Sequence[str] | None = "811510926611"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop bill_id column (unique constraint is dropped with the column in PostgreSQL) # noqa: E501
    op.drop_column("bill", "bill_id")
    # Add bill_number
    op.add_column(
        "bill",
        sa.Column("bill_number", sa.String(length=15), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("bill", "bill_number")
    op.add_column(
        "bill",
        sa.Column("bill_id", sa.UUID(), nullable=False),
    )
    # Restore unique constraint on bill_id if needed; for downgrade we just add column # noqa: E501
    # (existing rows would need values - typically downgrade is used with care)
    op.create_unique_constraint("bill_bill_id_key", "bill", ["bill_id"])
