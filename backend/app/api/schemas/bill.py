from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    model_validator,
)


class BillStatus(str, Enum):
    DRAFT = "DRAFT"  # 待寄送/草稿。系統已產生帳單金額，但還沒發送給客戶（檢查期）。
    SENT = "SENT"  # 已寄出。已寄給客戶，等待對方付款中。
    PROCESSING = (
        "PROCESSING"  # 對帳中/處理中。客戶回報已匯款，但我們尚未刷本子或確認款項入帳。
    )
    PAID = "PAID"  # 已結案/已領款。確認款項入帳，此筆交易正式完成。
    OVERDUE = "OVERDUE"  # 已逾期。超過約定的繳費期限，客戶仍未付款。
    CANCELLED = "CANCELLED"  # 已作廢。因故取消交易，例如合約終止、客戶取消訂單等。


class BillNote(BaseModel):
    content: str
    created_at: datetime = Field(default_factory=datetime.now)


class Bill(BaseModel):
    bill_id: UUID = Field(..., description="Unique invoice identifier")
    customer_id: UUID = Field(..., description="Customer ID (foreign key)")
    contract_id: UUID = Field(..., description="Contract ID (foreign key)")
    amount: float = Field(..., gt=0, description="Total billing amount")
    status: BillStatus = Field(default=BillStatus.DRAFT)
    notes: list[BillNote] = []

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    due_date: datetime = Field(..., description="Payment deadline")
    sent_at: datetime | None = None
    paid_at: datetime | None = None

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
            BillStatus.DRAFT: [BillStatus.SENT, BillStatus.CANCELLED],
            BillStatus.SENT: [
                BillStatus.PROCESSING,
                BillStatus.PAID,
                BillStatus.OVERDUE,
                BillStatus.CANCELLED,
            ],
            BillStatus.PROCESSING: [BillStatus.PAID, BillStatus.SENT],
            BillStatus.OVERDUE: [BillStatus.PAID, BillStatus.CANCELLED],
            BillStatus.PAID: [],  # 已結案不可變動
            BillStatus.CANCELLED: [],  # 已作廢不可變動
        }
        return next_status in allowed_paths.get(self.status, [])


class BillRead(Bill):
    id: UUID | None = Field(None, description="Bill ID")
    created_at: datetime | None = Field(None, description="Bill creation time")
    updated_at: datetime | None = Field(None, description="Bill last update time")  # noqa: E501

    model_config = ConfigDict(from_attributes=True)


class BillWrite(Bill):
    pass


class BillUpdate(Bill):
    pass
