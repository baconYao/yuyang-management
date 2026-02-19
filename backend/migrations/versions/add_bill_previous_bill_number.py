# flake8: noqa: E501
"""add bill previous_bill_number (self-ref to previous bill under same contract)

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2026-02-12

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e0f1a2b3c4d5"
down_revision: str | Sequence[str] | None = "d9e0f1a2b3c4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "bill",
        sa.Column(
            "previous_bill_number",
            sa.String(15),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "bill_previous_bill_number_fkey",
        "bill",
        "bill",
        ["previous_bill_number"],
        ["bill_number"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "bill_previous_bill_number_fkey",
        "bill",
        type_="foreignkey",
    )
    op.drop_column("bill", "previous_bill_number")
