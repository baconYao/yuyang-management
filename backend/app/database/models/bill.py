from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.dialects import postgresql
from sqlmodel import Column, Field, SQLModel

from app.api.schemas.bill import BillStatus
from app.api.schemas.contract import InvoiceType


class Bill(SQLModel, table=True):
    __tablename__ = "bill"

    bill_number: str = Field(
        sa_column=Column(String(15), primary_key=True),
        description="Bill number (primary key, e.g., B-2024-11-asdfg)",
    )
    customer_id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            ForeignKey("customer.id"),
            nullable=False,
        ),
        description="Customer ID (foreign key)",
    )
    contract_id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            ForeignKey("contract.id"),
            nullable=False,
        ),
        description="Contract ID (foreign key)",
    )
    amount: float = Field(
        sa_column=Column(postgresql.DOUBLE_PRECISION, nullable=False),
        description="Total billing amount",
    )
    tax_amount: float = Field(
        sa_column=Column(
            postgresql.DOUBLE_PRECISION, nullable=False, server_default="0"
        ),
        default=0.0,
        description="Tax amount",
    )
    monthly_rent: float = Field(
        sa_column=Column(postgresql.DOUBLE_PRECISION, nullable=False),
        description="Monthly rent",
    )
    invoice_type: InvoiceType = Field(
        sa_column=Column(
            postgresql.ENUM(
                InvoiceType,
                name="invoicetype",
                create_type=False,
            ),
            nullable=False,
            server_default="NO_INVOICE",
        ),
        default=InvoiceType.NO_INVOICE,
        description="Invoice type (e.g. no invoice, duplicate/triple uniform invoice)",  # noqa: E501
    )
    status: BillStatus = Field(
        sa_column=Column(
            postgresql.ENUM(
                BillStatus,
                name="billstatus",
                create_type=True,
            ),
            nullable=False,
            server_default="DRAFT",
        ),
        default=BillStatus.DRAFT,
        description="Bill status",
    )
    notes: str = Field(
        sa_column=Column(String(200), nullable=False, server_default=""),
        default="",
        description="Notes (plain text, max 200 characters)",
    )
    previous_bill_number: str | None = Field(
        default=None,
        sa_column=Column(
            String(15),
            ForeignKey("bill.bill_number"),
            nullable=True,
        ),
        description=(
            "Bill number of the previous bill under the same contract; "
            "null for the first bill."
        ),
    )
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        ),
        description="Creation time",
    )
    updated_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
            onupdate=datetime.now,
        ),
        description="Last update time",
    )
    due_date: datetime | None = Field(
        sa_column=Column(postgresql.TIMESTAMP, nullable=True),
        default=None,
        description="Payment deadline",
    )
    sent_at: datetime | None = Field(
        sa_column=Column(postgresql.TIMESTAMP, nullable=True),
        default=None,
        description="When the bill was sent",
    )
    paid_at: datetime | None = Field(
        sa_column=Column(postgresql.TIMESTAMP, nullable=True),
        default=None,
        description="When the bill was paid",
    )
    items: list[dict] = Field(
        default_factory=list,
        sa_column=Column(
            postgresql.JSONB(),
            nullable=False,
            server_default=text("'[]'::jsonb"),
        ),
        description="Line items (品名、數量、單價、金額) as JSON array.",
    )
