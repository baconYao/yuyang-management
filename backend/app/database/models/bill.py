from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel

from app.api.schemas.bill import BillStatus


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
    notes: list[dict] = Field(
        sa_column=Column(JSONB, nullable=False, server_default="[]"),
        default_factory=list,
        description="List of bill notes (content, created_at)",
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
