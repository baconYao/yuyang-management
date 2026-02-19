"""Move bill line items into bill.items JSONB (single table); drop bill_item.

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-02-17

"""

import json
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a2b3c4d5e6f7"
down_revision: str | Sequence[str] | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "bill",
        sa.Column(
            "items",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )

    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT bill_number, id, product_name, quantity, unit_price, "
            "amount, sort_order FROM bill_item "
            "ORDER BY bill_number, sort_order, id"
        )
    ).fetchall()

    by_bill: dict[str, list[dict]] = {}
    for row in rows:
        bn = row[0]
        if bn not in by_bill:
            by_bill[bn] = []
        by_bill[bn].append(
            {
                "id": str(row[1]),
                "product_name": row[2] or "",
                "quantity": float(row[3]),
                "unit_price": float(row[4]),
                "amount": float(row[5]),
                "sort_order": int(row[6]),
            }
        )

    for bill_number, items_list in by_bill.items():
        conn.execute(
            sa.text(
                "UPDATE bill SET items = CAST(:items AS jsonb) WHERE bill_number = :bn"
            ),
            {"items": json.dumps(items_list), "bn": bill_number},
        )

    op.drop_table("bill_item")


def downgrade() -> None:
    op.create_table(
        "bill_item",
        sa.Column("id", postgresql.UUID(), nullable=False),
        sa.Column("bill_number", sa.String(15), nullable=False),
        sa.Column("product_name", sa.String(200), nullable=False, server_default=""),
        sa.Column(
            "quantity",
            sa.DOUBLE_PRECISION(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "unit_price",
            sa.DOUBLE_PRECISION(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "amount",
            sa.DOUBLE_PRECISION(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["bill_number"],
            ["bill.bill_number"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    conn = op.get_bind()
    bills = conn.execute(sa.text("SELECT bill_number, items FROM bill")).fetchall()
    for bill_number, items_json in bills:
        if not items_json:
            continue
        for item in items_json:
            conn.execute(
                sa.text(
                    "INSERT INTO bill_item (id, bill_number, product_name, "
                    "quantity, unit_price, amount, sort_order) "
                    "VALUES (:id::uuid, :bn, :pn, :qty, :up, :amt, :so)"
                ),
                {
                    "id": item["id"],
                    "bn": bill_number,
                    "pn": item.get("product_name", ""),
                    "qty": item.get("quantity", 0),
                    "up": item.get("unit_price", 0),
                    "amt": item.get("amount", 0),
                    "so": item.get("sort_order", 0),
                },
            )

    op.drop_column("bill", "items")
