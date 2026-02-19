from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.dialects import postgresql
from sqlmodel import Column, Field, SQLModel

from app.api.schemas.customer import CustomerStatus, CustomerType


class Customer(SQLModel, table=True):
    __tablename__ = "customer"

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

    customer_name: str
    invoice_title: str | None = None
    invoice_number: str | None = None
    contact_phone: str
    messaging_app_line: str | None = None
    address: str
    primary_contact: str
    customer_type: CustomerType
    status: CustomerStatus = Field(
        default=CustomerStatus.ACTIVE,
        sa_column=Column(
            postgresql.ENUM(
                CustomerStatus,
                name="customerstatus",
                create_type=True,
            ),
            nullable=False,
            server_default="ACTIVE",
        ),
    )
