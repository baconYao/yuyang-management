import logging
from datetime import datetime

from app.api.schemas.bill import Bill, BillStatus

logger = logging.getLogger(__name__)


def mark_as_paid(bill: Bill) -> None:
    """
    檢查「狀態轉移」是否合法
    """
    if bill.can_transition_to(BillStatus.PAID):
        bill.status = BillStatus.PAID
        bill.paid_at = datetime.now()
        logger.info(f"Bill {bill.bill_id} marked as PAID")
        return
    raise ValueError(f"Cannot mark as PAID from current status: {bill.status}")
