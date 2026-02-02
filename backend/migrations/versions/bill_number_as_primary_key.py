"""bill_number as primary key, drop id

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-01-31

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e4f5a6b7c8d9"
down_revision: str | Sequence[str] | None = "d3e4f5a6b7c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1) Backfill bill_number where NULL (existing rows get placeholder)
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE bill
            SET bill_number = 'B-70-01-' || substr(md5(id::text), 1, 5)
            WHERE bill_number IS NULL
        """)
    )
    # 2) Make bill_number NOT NULL
    op.alter_column(
        "bill",
        "bill_number",
        existing_type=sa.String(15),
        nullable=False,
    )
    # 3) Drop primary key on id
    op.drop_constraint("bill_pkey", "bill", type_="primary")
    # 4) Add primary key on bill_number
    op.create_primary_key("bill_pkey", "bill", ["bill_number"])
    # 5) Drop column id
    op.drop_column("bill", "id")


def downgrade() -> None:
    op.add_column(
        "bill",
        sa.Column("id", sa.UUID(), nullable=True),
    )
    conn = op.get_bind()
    # Generate UUIDs for existing rows (PostgreSQL gen_random_uuid())
    conn.execute(sa.text("UPDATE bill SET id = gen_random_uuid() WHERE id IS NULL"))
    op.alter_column("bill", "id", nullable=False)
    op.drop_constraint("bill_pkey", "bill", type_="primary")
    op.create_primary_key("bill_pkey", "bill", ["id"])
    op.alter_column(
        "bill",
        "bill_number",
        existing_type=sa.String(15),
        nullable=True,
    )
