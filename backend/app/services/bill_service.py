import logging
import random
import string
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.bill import (
    BillItemRead,
    BillRead,
    BillStatus,
    BillUpdate,
    BillWrite,
)
from app.api.schemas.contract import InvoiceType
from app.database.models.bill import Bill
from app.database.models.contract import Contract
from app.database.models.customer import Customer

logger = logging.getLogger(__name__)


class InvalidStatusTransitionError(ValueError):
    """Raised when a bill status transition is not allowed."""


def _generate_bill_number() -> str:
    """Generate bill_number: B-<Year>-<Month>-<5 random uppercase letters>."""
    today = date.today()
    suffix = "".join(random.choices(string.ascii_uppercase, k=5))
    return f"B-{today.year}-{today.month:02d}-{suffix}"


class BillService:
    """Bill service for managing bill data in database"""

    def __init__(self, session: AsyncSession):
        """Initialize the service with database session"""
        self._session = session

    def _items_from_db(self, raw: list[dict] | None) -> list[BillItemRead]:
        """Convert bill.items JSON (list of dicts) to list[BillItemRead]."""
        if not raw:
            return []
        out = []
        for d in raw:
            if not isinstance(d, dict):
                continue
            out.append(
                BillItemRead(
                    product_name=d.get("product_name", ""),
                    quantity=float(d.get("quantity", 0)),
                    unit_price=float(d.get("unit_price", 0)),
                    amount=float(d.get("amount", 0)),
                    sort_order=int(d.get("sort_order", 0)),
                )
            )
        out.sort(key=lambda x: x.sort_order)
        return out

    def _bill_to_read(self, db_bill: Bill) -> BillRead:
        """Build BillRead from Bill ORM (items from db_bill.items JSONB)."""
        read = BillRead.model_validate(db_bill)
        read.items = self._items_from_db(getattr(db_bill, "items", None))
        return read

    async def get_by_bill_number(self, bill_number: str) -> BillRead | None:
        """
        Get a bill by bill_number (table primary key).

        Args:
            bill_number: The bill number (primary key) of the bill to retrieve

        Returns:
            BillRead if found, None otherwise
        """
        if not bill_number:
            return None
        statement = select(Bill).where(Bill.bill_number == bill_number)
        result = await self._session.execute(statement)
        db_bill = result.scalar_one_or_none()
        if db_bill is None:
            return None
        return self._bill_to_read(db_bill)

    async def get_bill_with_customer(
        self, bill_number: str
    ) -> tuple[BillRead, Customer] | None:
        """
        Get a bill and its customer by bill_number.

        Args:
            bill_number: The bill number (primary key) of the bill to retrieve

        Returns:
            (BillRead, Customer) if both found, None if bill or customer missing # noqa: E501
        """
        bill_read = await self.get_by_bill_number(bill_number)
        if bill_read is None:
            return None
        cust_result = await self._session.execute(
            select(Customer).where(Customer.id == bill_read.customer_id)
        )
        db_customer = cust_result.scalar_one_or_none()
        if db_customer is None:
            return None
        return (bill_read, db_customer)

    async def get_all(
        self,
        customer_id: UUID | None = None,
        contract_id: UUID | None = None,
        statuses: list[BillStatus] | None = None,
    ) -> list[BillRead]:
        """
        Get all bills, optionally filtered by customer_id, contract_id, or statuses. # noqa: E501

        Args:
            customer_id: Optional customer ID to filter bills
            contract_id: Optional contract ID to filter bills
            statuses: Optional list of BillStatus to filter bills (e.g. [DRAFT], [PAID, OVERDUE, CANCELLED])

        Returns:
            List of bills
        """
        statement = select(Bill)
        if customer_id is not None:
            statement = statement.where(Bill.customer_id == customer_id)
        if contract_id is not None:
            statement = statement.where(Bill.contract_id == contract_id)
        if statuses:
            statement = statement.where(Bill.status.in_(statuses))
        statement = statement.order_by(desc(Bill.created_at))
        result = await self._session.execute(statement)
        db_bills = result.scalars().all()
        return [self._bill_to_read(b) for b in db_bills]

    async def create(self, bill: BillWrite) -> BillRead | None:
        """
        Create a new bill.

        Args:
            bill: Bill data to create

        Returns:
            Created bill with assigned bill_number, or None if customer/contract not found  # noqa: E501
        """
        if bill is None:
            return None

        # Verify customer exists
        cust_result = await self._session.execute(
            select(Customer).where(Customer.id == bill.customer_id)
        )
        if cust_result.scalar_one_or_none() is None:
            logger.warning(
                f"Failed to create bill: customer_id {bill.customer_id} does not exist"  # noqa: E501
            )
            return None

        # Verify contract exists
        contract_result = await self._session.execute(
            select(Contract).where(Contract.id == bill.contract_id)
        )
        if contract_result.scalar_one_or_none() is None:
            logger.warning(
                f"Failed to create bill: contract_id {bill.contract_id} does not exist"  # noqa: E501
            )
            return None

        # System auto-fill: previous bill under the same contract (latest by created_at) # noqa: E501
        prev_result = await self._session.execute(
            select(Bill.bill_number)
            .where(Bill.contract_id == bill.contract_id)
            .order_by(desc(Bill.created_at))
            .limit(1)
        )
        previous_bill_number = prev_result.scalar_one_or_none()

        db_bill = Bill(
            bill_number=_generate_bill_number(),
            customer_id=bill.customer_id,
            contract_id=bill.contract_id,
            amount=bill.amount,
            tax_amount=bill.tax_amount,
            monthly_rent=bill.monthly_rent,
            invoice_type=bill.invoice_type,
            status=bill.status,
            notes=bill.notes or "",
            previous_bill_number=previous_bill_number,
        )
        if bill.items:
            items_json = [
                {
                    "product_name": item.product_name or "",
                    "quantity": float(item.quantity),
                    "unit_price": float(item.unit_price),
                    "amount": float(item.amount),
                    "sort_order": getattr(item, "sort_order", i),
                }
                for i, item in enumerate(bill.items)
            ]
            db_bill.items = items_json
        self._session.add(db_bill)
        await self._session.commit()
        await self._session.refresh(db_bill)
        return self._bill_to_read(db_bill)

    def create_first_bill_for_contract(self, db_contract: Contract) -> None:
        """
        Build and add the first bill for a contract (e.g. when status becomes ACTIVE). # noqa: E501
        Does not commit; caller must commit to keep same transaction.
        """
        interval_months = int(db_contract.billing_interval.value)
        monthly_rent = float(db_contract.monthly_rent)
        amount = monthly_rent * interval_months
        invoice_type = (
            db_contract.invoice_type
            if db_contract.invoice_type is not None
            else InvoiceType.NO_INVOICE
        )
        items_json = [
            {
                "product_name": db_contract.product_name or "",
                "quantity": float(interval_months),
                "unit_price": monthly_rent,
                "amount": amount,
                "sort_order": 0,
            }
        ]
        db_bill = Bill(
            bill_number=_generate_bill_number(),
            customer_id=db_contract.customer_id,
            contract_id=db_contract.id,
            amount=amount,
            tax_amount=0.0,
            monthly_rent=monthly_rent,
            invoice_type=invoice_type,
            status=BillStatus.DRAFT,
            notes="",
            previous_bill_number=None,
            items=items_json,
        )
        self._session.add(db_bill)

    async def update(self, bill_number: str, bill_update: BillUpdate) -> BillRead:  # noqa: E501
        """
        Update a bill by bill_number (primary key).

        Args:
            bill_number: The bill number (primary key) of the bill to update
            bill_update: Bill data to update (partial update supported)

        Returns:
            BillRead if bill was updated

        Raises:
            ValueError: If bill not found
        """
        if not bill_number:
            raise ValueError("Bill number cannot be empty")

        result = await self._session.execute(
            select(Bill).where(Bill.bill_number == bill_number)
        )
        db_bill = result.scalar_one_or_none()
        if db_bill is None:
            raise ValueError(f"Bill with bill_number {bill_number!r} not found")  # noqa: E501

        update_data = bill_update.model_dump(exclude_unset=True)
        update_data.pop("bill_number", None)  # never update primary key
        items_payload: list[dict] | None = update_data.pop("items", None)

        # Validate status transition if status is being updated
        if "status" in update_data:
            new_status = update_data["status"]
            current_bill_read = self._bill_to_read(db_bill)
            if not current_bill_read.can_transition_to(new_status):
                raise InvalidStatusTransitionError(
                    f"Invalid status transition from {db_bill.status!s} to {new_status!s}"  # noqa: E501
                )

        for field, value in update_data.items():
            if isinstance(value, datetime) and value.tzinfo is not None:
                value = value.astimezone(UTC).replace(tzinfo=None)
            if field == "notes" and value is None:
                value = ""
            setattr(db_bill, field, value)

        if items_payload is not None:
            items_json = []
            for sort_order, item in enumerate(items_payload):
                items_json.append(
                    {
                        "product_name": item.get("product_name") or "",
                        "quantity": float(item.get("quantity", 0)),
                        "unit_price": float(item.get("unit_price", 0)),
                        "amount": float(item.get("amount", 0)),
                        "sort_order": item.get("sort_order", sort_order),
                    }
                )
            db_bill.items = items_json

        await self._session.commit()
        await self._session.refresh(db_bill)
        return self._bill_to_read(db_bill)
