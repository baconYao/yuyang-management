"""add bill tax_amount, monthly_rent, invoice_type

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
Create Date: 2026-02-12

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d9e0f1a2b3c4"
down_revision: str | Sequence[str] | None = "c8d9e0f1a2b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # invoicetype ENUM already exists (created by add_contract_invoice_type)
    invoicetype = postgresql.ENUM(
        "NO_INVOICE",
        "DUPLICATE_UNIFORM_INVOICE",
        "TRIPLE_UNIFORM_INVOICE",
        name="invoicetype",
        create_type=False,
    )
    op.add_column(
        "bill",
        sa.Column(
            "tax_amount",
            sa.DOUBLE_PRECISION(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "bill",
        sa.Column(
            "monthly_rent",
            sa.DOUBLE_PRECISION(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "bill",
        sa.Column(
            "invoice_type",
            invoicetype,
            nullable=False,
            server_default="NO_INVOICE",
        ),
    )


def downgrade() -> None:
    op.drop_column("bill", "invoice_type")
    op.drop_column("bill", "monthly_rent")
    op.drop_column("bill", "tax_amount")
