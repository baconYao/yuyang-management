"""Allow null for customer invoice_title, invoice_number, messaging_app_line.

Revision ID: b2c3d4e5f6a7
Revises: a2b3c4d5e6f7
Create Date: 2026-02-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a2b3c4d5e6f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "customer",
        "invoice_title",
        existing_type=sa.String(),
        nullable=True,
    )
    op.alter_column(
        "customer",
        "invoice_number",
        existing_type=sa.String(),
        nullable=True,
    )
    op.alter_column(
        "customer",
        "messaging_app_line",
        existing_type=sa.String(),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "customer",
        "invoice_title",
        existing_type=sa.String(),
        nullable=False,
    )
    op.alter_column(
        "customer",
        "invoice_number",
        existing_type=sa.String(),
        nullable=False,
    )
    op.alter_column(
        "customer",
        "messaging_app_line",
        existing_type=sa.String(),
        nullable=False,
    )
