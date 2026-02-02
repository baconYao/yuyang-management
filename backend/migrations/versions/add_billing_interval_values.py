# flake8: noqa: E501
"""add billing interval enum values: ONE_MONTH, TWO_MONTHS, THIRTY_SIX_MONTHS

Revision ID: b7c8d9e0f1a2
Revises: a6b7c8d9e0f1
Create Date: 2026-01-31

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7c8d9e0f1a2"
down_revision: str | Sequence[str] | None = "a6b7c8d9e0f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # PostgreSQL stores enum member names; add new BillingInterval members.
    op.execute("ALTER TYPE billinginterval ADD VALUE IF NOT EXISTS 'ONE_MONTH'")
    op.execute("ALTER TYPE billinginterval ADD VALUE IF NOT EXISTS 'TWO_MONTHS'")
    op.execute("ALTER TYPE billinginterval ADD VALUE IF NOT EXISTS 'THIRTY_SIX_MONTHS'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values; leave as-is.
    pass
