"""add contract invoice_type

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2025-01-30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c2d3e4f5a6b7"
down_revision: str | Sequence[str] | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    invoicetype = postgresql.ENUM(
        "NO_INVOICE",
        "DUPLICATE_UNIFORM_INVOICE",
        "TRIPLE_UNIFORM_INVOICE",
        name="invoicetype",
    )
    invoicetype.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "contract",
        sa.Column(
            "invoice_type",
            invoicetype,
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("contract", "invoice_type")
    postgresql.ENUM(name="invoicetype").drop(op.get_bind(), checkfirst=True)
