"""add customer status

Revision ID: b1c2d3e4f5a6
Revises: ea68ff45c522
Create Date: 2025-01-30

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision: str | Sequence[str] | None = "ea68ff45c522"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    customerstatus = postgresql.ENUM(
        "ACTIVE",
        "TERMINATED",
        name="customerstatus",
    )
    customerstatus.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "customer",
        sa.Column(
            "status",
            customerstatus,
            nullable=False,
            server_default="ACTIVE",
        ),
    )


def downgrade() -> None:
    op.drop_column("customer", "status")
    postgresql.ENUM(name="customerstatus").drop(op.get_bind(), checkfirst=True)
