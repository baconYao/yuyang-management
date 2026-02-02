import logging
import random
import string
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.bill import BillRead, BillUpdate, BillWrite
from app.database.models.bill import Bill
from app.database.models.contract import Contract
from app.database.models.customer import Customer

logger = logging.getLogger(__name__)


class InvalidStatusTransitionError(ValueError):
    """Raised when a bill status transition is not allowed."""


def _generate_bill_number() -> str:
    """Generate bill_number: B-<Year>-<Month>-<5 random lowercase letters>."""
    today = date.today()
    suffix = "".join(random.choices(string.ascii_uppercase, k=5))
    return f"B-{today.year}-{today.month:02d}-{suffix}"


class BillService:
    """Bill service for managing bill data in database"""

    def __init__(self, session: AsyncSession):
        """Initialize the service with database session"""
        self._session = session

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
        return BillRead.model_validate(db_bill)

    async def get_all(
        self,
        customer_id: UUID | None = None,
        contract_id: UUID | None = None,
    ) -> list[BillRead]:
        """
        Get all bills, optionally filtered by customer_id or contract_id.

        Args:
            customer_id: Optional customer ID to filter bills
            contract_id: Optional contract ID to filter bills

        Returns:
            List of bills
        """
        statement = select(Bill)
        if customer_id is not None:
            statement = statement.where(Bill.customer_id == customer_id)
        if contract_id is not None:
            statement = statement.where(Bill.contract_id == contract_id)
        result = await self._session.execute(statement)
        db_bills = result.scalars().all()
        return [BillRead.model_validate(b) for b in db_bills]

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

        db_bill = Bill(
            bill_number=_generate_bill_number(),
            customer_id=bill.customer_id,
            contract_id=bill.contract_id,
            amount=bill.amount,
            status=bill.status,
            notes=bill.notes or "",
        )
        self._session.add(db_bill)
        await self._session.commit()
        await self._session.refresh(db_bill)
        return BillRead.model_validate(db_bill)

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

        # Validate status transition if status is being updated
        if "status" in update_data:
            new_status = update_data["status"]
            current_bill_read = BillRead.model_validate(db_bill)
            if not current_bill_read.can_transition_to(new_status):
                raise InvalidStatusTransitionError(
                    f"Invalid status transition from {db_bill.status!s} to {new_status!s}"  # noqa: E501
                )

        for field, value in update_data.items():
            setattr(db_bill, field, value)

        await self._session.commit()
        await self._session.refresh(db_bill)
        return BillRead.model_validate(db_bill)
