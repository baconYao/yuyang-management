import logging
import random
import string
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.bill import (
    BillItemRead,
    BillItemWrite,
    BillRead,
    BillStatus,
    BillUpdate,
    BillWrite,
)
from app.database.models.bill import Bill, BillItem
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

    async def _get_items_for_bill(self, bill_number: str) -> list[BillItem]:
        """Load bill line items for a bill, ordered by sort_order."""
        statement = (
            select(BillItem)
            .where(BillItem.bill_number == bill_number)
            .order_by(BillItem.sort_order, BillItem.id)
        )
        result = await self._session.execute(statement)
        return list(result.scalars().all())

    def _bill_to_read(self, db_bill: Bill, items: list[BillItem]) -> BillRead:
        """Build BillRead from Bill ORM and its line items."""
        read = BillRead.model_validate(db_bill)
        read.items = [BillItemRead.model_validate(i) for i in items]
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
        items = await self._get_items_for_bill(db_bill.bill_number)
        return self._bill_to_read(db_bill, items)

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
        out = []
        for b in db_bills:
            items = await self._get_items_for_bill(b.bill_number)
            out.append(self._bill_to_read(b, items))
        return out

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
        self._session.add(db_bill)
        await self._session.commit()
        await self._session.refresh(db_bill)
        items = await self._get_items_for_bill(db_bill.bill_number)
        return self._bill_to_read(db_bill, items)

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
        items_payload: list[BillItemWrite] | None = update_data.pop("items", None)  # noqa: E501

        # Validate status transition if status is being updated
        if "status" in update_data:
            new_status = update_data["status"]
            current_bill_read = self._bill_to_read(
                db_bill, await self._get_items_for_bill(db_bill.bill_number)
            )
            if not current_bill_read.can_transition_to(new_status):
                raise InvalidStatusTransitionError(
                    f"Invalid status transition from {db_bill.status!s} to {new_status!s}"  # noqa: E501
                )

        for field, value in update_data.items():
            if isinstance(value, datetime) and value.tzinfo is not None:
                value = value.astimezone(UTC).replace(tzinfo=None)
            setattr(db_bill, field, value)

        if items_payload is not None:
            to_delete = (
                (
                    await self._session.execute(
                        select(BillItem).where(BillItem.bill_number == bill_number)  # noqa: E501
                    )
                )
                .scalars()
                .all()
            )
            for row in to_delete:
                await self._session.delete(row)
            for sort_order, item in enumerate(items_payload):
                item_id = item.get("id")
                self._session.add(
                    BillItem(
                        id=UUID(str(item_id)) if item_id else uuid4(),
                        bill_number=bill_number,
                        product_name=item.get("product_name") or "",
                        quantity=item.get("quantity", 0),
                        unit_price=item.get("unit_price", 0),
                        amount=item.get("amount", 0),
                        sort_order=item.get("sort_order", sort_order),
                    )
                )

        await self._session.commit()
        await self._session.refresh(db_bill)
        items = await self._get_items_for_bill(db_bill.bill_number)
        return self._bill_to_read(db_bill, items)
