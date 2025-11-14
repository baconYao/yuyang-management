from enum import Enum

from pydantic import BaseModel, Field


class CustomerType(str, Enum):
    """Customer type enumeration"""

    REAL_ESTATE = "REAL_ESTATE"
    EDUCATION = "EDUCATION"
    ELEMENTARY_ATTACHED_KINDERGARTEN = "ELEMENTARY_ATTACHED_KINDERGARTEN"
    COMPANY = "COMPANY"
    INSURANCE = "INSURANCE"
    OTHER = "OTHER"


class BaseCustomer(BaseModel):
    """Base customer information schema"""

    customer_name: str | None = Field(None, description="Customer name")
    invoice_title: str | None = Field(None, description="Invoice title")
    invoice_number: str | None = Field(None, description="Invoice number")
    contact_phone: str | None = Field(None, description="Contact phone number")
    messaging_app: str | None = Field(None, description="Messaging app (Line, etc.)")  # noqa: E501
    address: str | None = Field(None, description="Address")
    primary_contact: str | None = Field(None, description="Primary contact person")  # noqa: E501
    customer_type: CustomerType | None = Field(None, description="Customer type")  # noqa: E501


class CustomerRead(BaseCustomer):
    """Customer information read schema"""

    id: int | None = Field(None, description="Customer ID")

    class Config:
        from_attributes = True


class CustomerWrite(BaseCustomer):
    """Customer information write schema"""

    customer_name: str = Field(..., description="Customer name", min_length=1)


class CustomerUpdate(BaseCustomer):
    """Customer information update schema"""

    customer_name: str | None = Field(None, description="Customer name", min_length=1)  # noqa: E501
