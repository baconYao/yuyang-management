# flake8: noqa: E501

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ContractStatus(str, Enum):
    """Contract status enumeration"""

    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED"
    PENDING = "PENDING"
    SUSPENDED = "SUSPENDED"


class PaymentMethod(str, Enum):
    """Payment method enumeration"""

    BANK_TRANSFER = "BANK_TRANSFER"
    CASH = "CASH"
    CHECK = "CHECK"
    OTHER = "OTHER"


class BillingInterval(str, Enum):
    """Billing interval enumeration"""

    THREE_MONTHS = "3"
    SIX_MONTHS = "6"
    TWELVE_MONTHS = "12"
    TWENTY_FOUR_MONTHS = "24"


class BaseContract(BaseModel):
    """Base contract information schema"""

    customer_id: UUID = Field(..., description="Customer ID (foreign key)")
    product_name: str = Field(
        ..., max_length=30, description="Product name (max 30 characters)"
    )
    start_date: datetime = Field(..., description="Contract start date")
    end_date: datetime = Field(..., description="Contract end date")
    monthly_rent: int = Field(..., description="Monthly rent amount")
    billing_interval: BillingInterval = Field(
        ..., description="Billing interval (3, 6, 12, or 24 months)"
    )
    notes: str | None = Field(
        None, max_length=300, description="Notes (max 300 characters)"
    )
    status: ContractStatus = Field(..., description="Contract status")
    contract_number: str | None = Field(
        None, description="Contract number (e.g., CONTRACT-2024-001)"
    )
    # 合約簽署日期，不為合約開始日期
    signed_date: datetime | None = Field(None, description="Contract signed date")
    payment_method: PaymentMethod | None = Field(None, description="Payment method")
    next_billing_date: datetime | None = Field(None, description="Next billing date")
    # 合約終止日期
    terminated_at: datetime | None = Field(
        None, description="Contract termination date"
    )
    termination_reason: str | None = Field(
        None, description="Contract termination reason"
    )


class ContractRead(BaseContract):
    """Contract information read schema"""

    id: UUID | None = Field(None, description="Contract ID")
    created_at: datetime | None = Field(None, description="Contract creation time")
    updated_at: datetime | None = Field(None, description="Contract last update time")

    model_config = ConfigDict(from_attributes=True)


class ContractWrite(BaseContract):
    """Contract information write schema"""

    pass


class ContractUpdate(BaseModel):
    """Contract information update schema"""

    billing_interval: BillingInterval | None = Field(
        None, description="Billing interval (3, 6, 12, or 24 months)"
    )
    notes: str | None = Field(
        None, max_length=300, description="Notes (max 300 characters)"
    )
    status: ContractStatus | None = Field(None, description="Contract status")
    payment_method: PaymentMethod | None = Field(None, description="Payment method")
    next_billing_date: datetime | None = Field(None, description="Next billing date")
    terminated_at: datetime | None = Field(
        None, description="Contract termination date"
    )
    termination_reason: str | None = Field(
        None, description="Contract termination reason"
    )
