# flake8: noqa: E501
"""bill.notes: JSONB -> VARCHAR(200)

Revision ID: a6b7c8d9e0f1
Revises: f5a6b7c8d9e0
Create Date: 2026-01-31

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a6b7c8d9e0f1"
down_revision: str | Sequence[str] | None = "f5a6b7c8d9e0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "bill",
        sa.Column(
            "notes_str", sa.String(length=200), nullable=False, server_default=""
        ),
    )
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE bill
            SET notes_str = LEFT(
                COALESCE(notes->0->>'content', ''),
                200
            )
            WHERE jsonb_typeof(notes) = 'array' AND jsonb_array_length(notes) > 0
        """)
    )
    op.drop_column("bill", "notes")
    op.alter_column(
        "bill",
        "notes_str",
        new_column_name="notes",
    )


def downgrade() -> None:
    # After upgrade we have column "notes" (VARCHAR). Rename to notes_str, add JSONB notes, copy, drop notes_str.
    op.alter_column(
        "bill",
        "notes",
        new_column_name="notes_str",
    )
    op.add_column(
        "bill",
        sa.Column(
            "notes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default="[]",
            nullable=False,
        ),
    )
    conn = op.get_bind()
    conn.execute(
        sa.text("""
            UPDATE bill
            SET notes = jsonb_build_array(
                jsonb_build_object('content', COALESCE(notes_str, ''), 'created_at', null)
            )
        """)
    )
    op.drop_column("bill", "notes_str")
