"""add bill_item table for bill line items (品名、數量、單價、金額)

Revision ID: f1a2b3c4d5e6
Revises: e0f1a2b3c4d5
Create Date: 2026-02-12

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "e0f1a2b3c4d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bill_item",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("bill_number", sa.String(15), nullable=False),
        sa.Column("product_name", sa.String(200), nullable=False, server_default=""),
        sa.Column(
            "quantity", sa.DOUBLE_PRECISION(), nullable=False, server_default="0"
        ),
        sa.Column(
            "unit_price", sa.DOUBLE_PRECISION(), nullable=False, server_default="0"
        ),
        sa.Column("amount", sa.DOUBLE_PRECISION(), nullable=False, server_default="0"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["bill_number"],
            ["bill.bill_number"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("bill_item")
