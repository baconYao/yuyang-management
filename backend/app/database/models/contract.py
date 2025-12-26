from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects import postgresql
from sqlmodel import Column, Field, SQLModel

from app.api.schemas.contract import (
    BillingInterval,
    ContractStatus,
    PaymentMethod,
)


class Contract(SQLModel, table=True):
    __tablename__ = "contract"

    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
            onupdate=datetime.now,
        )
    )

    customer_id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            ForeignKey("customer.id"),
            nullable=False,
        ),
        description="Customer ID (foreign key)",
    )
    product_name: str = Field(
        sa_column=Column(String(30), nullable=False),
        description="Product name (max 30 characters)",
    )
    start_date: datetime = Field(
        sa_column=Column(postgresql.TIMESTAMP, nullable=False),
        description="Contract start date",
    )
    end_date: datetime = Field(
        sa_column=Column(postgresql.TIMESTAMP, nullable=False),
        description="Contract end date",
    )
    monthly_rent: int = Field(
        sa_column=Column(postgresql.INTEGER, nullable=False),
        description="Monthly rent amount",
    )
    billing_interval: BillingInterval = Field(
        sa_column=Column(
            postgresql.ENUM(
                BillingInterval,
                name="billinginterval",
                create_type=False,
            ),
            nullable=False,
        ),
        description="Billing interval (3, 6, 12, or 24 months)",
    )
    notes: str | None = Field(
        sa_column=Column(String(300), nullable=True),
        default=None,
        description="Notes (max 300 characters)",
    )
    status: ContractStatus = Field(
        sa_column=Column(
            postgresql.ENUM(
                ContractStatus,
                name="contractstatus",
                create_type=False,
            ),
            nullable=False,
        ),
        description="Contract status",
    )
    contract_number: str | None = Field(
        sa_column=Column(String, nullable=True),
        default=None,
        description="Contract number (e.g., CONTRACT-2024-001)",
    )
    signed_date: datetime | None = Field(
        sa_column=Column(postgresql.TIMESTAMP, nullable=True),
        default=None,
        description="Contract signed date",
    )
    payment_method: PaymentMethod | None = Field(
        sa_column=Column(
            postgresql.ENUM(
                PaymentMethod,
                name="paymentmethod",
                create_type=False,
            ),
            nullable=True,
        ),
        default=None,
        description="Payment method",
    )
    next_billing_date: datetime | None = Field(
        sa_column=Column(postgresql.TIMESTAMP, nullable=True),
        default=None,
        description="Next billing date",
    )
    terminated_at: datetime | None = Field(
        sa_column=Column(postgresql.TIMESTAMP, nullable=True),
        default=None,
        description="Contract termination date",
    )
    termination_reason: str | None = Field(
        sa_column=Column(String, nullable=True),
        default=None,
        description="Contract termination reason",
    )
