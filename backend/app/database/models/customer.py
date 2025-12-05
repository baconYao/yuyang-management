from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.dialects import postgresql
from sqlmodel import Column, Field, SQLModel

from app.api.schemas.customer import CustomerType


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
    invoice_title: str
    invoice_number: str
    contact_phone: str
    messaging_app_line: str
    address: str
    primary_contact: str
    customer_type: CustomerType
