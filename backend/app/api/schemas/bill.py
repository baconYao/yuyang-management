from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    model_validator,
)

from app.api.schemas.contract import InvoiceType


class BillStatus(StrEnum):
    DRAFT = "DRAFT"  # 待寄送/草稿。系統已產生帳單金額，但還沒發送給客戶（檢查期）。
    SENT = "SENT"  # 已寄出。已寄給客戶，等待對方付款中。
    PROCESSING = (
        "PROCESSING"  # 對帳中/處理中。客戶回報已匯款，但我們尚未刷本子或確認款項入帳。
    )
    PAID = "PAID"  # 已結案/已領款。確認款項入帳，此筆交易正式完成。
    OVERDUE = "OVERDUE"  # 已逾期。超過約定的繳費期限，客戶仍未付款。
    CANCELLED = "CANCELLED"  # 已作廢。因故取消交易，例如合約終止、客戶取消訂單等。


NOTES_MAX_LENGTH = 200

PRODUCT_NAME_MAX_LENGTH = 200


class BillItemRead(BaseModel):
    """Line item for a bill (品名、數量、單價、金額). No id stored."""

    product_name: str = Field(
        "", max_length=PRODUCT_NAME_MAX_LENGTH, description="品名"
    )
    quantity: float = Field(0, ge=0, description="數量")
    unit_price: float = Field(0, ge=0, description="單價")
    amount: float = Field(0, ge=0, description="金額")
    sort_order: int = Field(0, ge=0, description="Display order (0-based).")

    model_config = ConfigDict(from_attributes=True)


class BillItemWrite(BaseModel):
    """Create or update a bill line item. No id stored."""

    product_name: str = Field(
        "", max_length=PRODUCT_NAME_MAX_LENGTH, description="品名"
    )
    quantity: float = Field(0, ge=0, description="數量")
    unit_price: float = Field(0, ge=0, description="單價")
    amount: float = Field(0, ge=0, description="金額")
    sort_order: int = Field(0, ge=0, description="Display order (0-based).")


class Bill(BaseModel):
    customer_id: UUID = Field(..., description="Customer ID (foreign key)")
    contract_id: UUID = Field(..., description="Contract ID (foreign key)")
    amount: float = Field(..., gt=0, description="Total billing amount")
    tax_amount: float = Field(0, ge=0, description="Tax amount")
    invoice_type: InvoiceType = Field(
        default=InvoiceType.NO_INVOICE,
        description="Invoice type (e.g. no invoice, duplicate/triple uniform invoice)",  # noqa: E501
    )
    status: BillStatus = Field(default=BillStatus.DRAFT)
    notes: str = Field(
        "",
        max_length=NOTES_MAX_LENGTH,
        description="Notes (plain text, max 200 characters)",
    )
    bill_number: str | None = Field(
        None,
        description="Bill number, primary key (e.g., B-2024-11-asdfg); server-generated on create.",  # noqa: E501
        max_length=15,
    )
    previous_bill_number: str | None = Field(
        None,
        description="Bill number of the previous bill under the same contract; null for the first bill.",  # noqa: E501
        max_length=15,
    )

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    due_date: datetime | None = Field(None, description="Payment deadline")
    sent_at: datetime | None = None  # 帳單寄出時間
    paid_at: datetime | None = None  # 客戶付款時間

    @computed_field
    @property
    def can_edit_financials(self) -> bool:
        """只有當帳單狀態為 DRAFT 時，才能修改財務資料"""
        return self.status == BillStatus.DRAFT

    @computed_field
    @property
    def can_add_notes(self) -> bool:
        """備註通常隨時都能加，甚至 PAID 後也能註記收據編號"""
        return self.status != BillStatus.CANCELLED

    @model_validator(mode="after")
    def validate_status_timestamps(self) -> Bill:
        """
        驗證狀態與時間戳記的一致性
        """
        # 當狀態為 SENT，確保有寄出時間
        if self.status == BillStatus.SENT and not self.sent_at:
            self.sent_at = datetime.now()

        # 當狀態為 PAID，強制檢查是否有付款時間
        if self.status == BillStatus.PAID and not self.paid_at:
            raise ValueError("A 'PAID' bill must have a paid_at timestamp.")

        return self

    def can_transition_to(self, next_status: BillStatus) -> bool:
        """
        定義合法的狀態轉移路徑 (State Machine)
        """
        allowed_paths = {
            BillStatus.DRAFT: [
                BillStatus.DRAFT,
                BillStatus.SENT,
                BillStatus.CANCELLED,
            ],
            BillStatus.SENT: [
                BillStatus.SENT,
                BillStatus.PROCESSING,
                BillStatus.PAID,
                BillStatus.OVERDUE,
                BillStatus.CANCELLED,
            ],
            BillStatus.PROCESSING: [
                BillStatus.SENT,
                BillStatus.PROCESSING,
                BillStatus.PAID,
            ],
            BillStatus.OVERDUE: [BillStatus.PAID, BillStatus.CANCELLED],
            BillStatus.PAID: [],  # 已結案不可變動
            BillStatus.CANCELLED: [],  # 已作廢不可變動
        }
        return next_status in allowed_paths.get(self.status, [])


class BillRead(Bill):
    bill_number: str = Field(..., description="Bill number (primary key)")
    created_at: datetime | None = Field(None, description="Bill creation time")
    updated_at: datetime | None = Field(None, description="Bill last update time")  # noqa: E501
    items: list[BillItemRead] = Field(
        default_factory=list,
        description="Bill line items (品名、數量、單價、金額), ordered by sort_order.",
    )

    model_config = ConfigDict(from_attributes=True)


class BillWrite(BaseModel):
    customer_id: UUID = Field(..., description="Customer ID (foreign key)")
    contract_id: UUID = Field(..., description="Contract ID (foreign key)")
    amount: float = Field(..., gt=0, description="Total billing amount")
    tax_amount: float = Field(0, ge=0, description="Tax amount")
    invoice_type: InvoiceType = Field(
        default=InvoiceType.NO_INVOICE,
        description="Invoice type (e.g. no invoice, duplicate/triple uniform invoice)",  # noqa: E501
    )
    status: BillStatus = Field(default=BillStatus.DRAFT)
    notes: str = Field(
        "",
        max_length=NOTES_MAX_LENGTH,
        description="Notes (plain text, max 200 characters)",
    )
    items: list[BillItemWrite] | None = Field(
        None,
        description="Optional line items; if omitted, bill has no items.",
    )


class BillUpdate(BaseModel):
    """Only these fields are allowed to be updated."""

    status: BillStatus = Field(
        ..., description="Bill status (required, cannot be null)"
    )
    notes: str | None = Field(
        None,
        max_length=NOTES_MAX_LENGTH,
        description="Notes (plain text, max 200 characters)",
    )
    tax_amount: float | None = Field(None, ge=0, description="Tax amount")
    invoice_type: InvoiceType | None = Field(
        None,
        description="Invoice type (e.g. no invoice, duplicate/triple uniform invoice)",  # noqa: E501
    )
    due_date: datetime | None = Field(None, description="Payment deadline")
    sent_at: datetime | None = Field(None, description="帳單寄出時間")
    paid_at: datetime | None = Field(None, description="客戶付款時間")
    items: list[BillItemWrite] | None = Field(
        None,
        description="If set, replace bill line items with this list (ordered by sort_order).",  # noqa: E501
    )
