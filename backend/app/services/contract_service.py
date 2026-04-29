import calendar
import logging
import random
import string
from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.schemas.contract import (
    ContractRead,
    ContractStatus,
    ContractUpdate,
    ContractWrite,
)
from app.database.models.bill import Bill
from app.database.models.contract import Contract
from app.database.models.customer import Customer
from app.services.bill_service import BillService

logger = logging.getLogger(__name__)


def _generate_contract_number() -> str:
    """Generate contract_number: C-<Year>-<Month>-<5 random uppercase letters>."""  # noqa: E501
    today = date.today()
    suffix = "".join(random.choices(string.ascii_uppercase, k=5))
    return f"C-{today.year}-{today.month:02d}-{suffix}"


# DB uses TIMESTAMP WITHOUT TIME ZONE; normalize datetimes to naive UTC for storage. # noqa: E501
_CONTRACT_TIMESTAMP_FIELDS = frozenset(
    {"signed_date", "next_billing_date", "terminated_at"}
)


def _to_naive_utc(dt: datetime) -> datetime:
    """Return naive datetime for DB (UTC instant); no-op if already naive."""
    if getattr(dt, "tzinfo", None) is None:
        return dt
    return dt.astimezone(UTC).replace(tzinfo=None)


def _add_months(dt: datetime, months: int) -> datetime:
    """Return naive datetime equal to dt + months (handles month overflow, day clamp)."""  # noqa: E501
    dt = _to_naive_utc(dt)
    year, month, day = dt.year, dt.month, dt.day
    month += months
    while month > 12:
        month -= 12
        year += 1
    while month < 1:
        month += 12
        year -= 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(day, last_day)
    return datetime(
        year,
        month,
        day,
        dt.hour,
        dt.minute,
        dt.second,
        dt.microsecond,
    )


def _compute_bill_dates(
    start_date: datetime,
    end_date: datetime,
    interval_months: int,
) -> list[datetime]:
    """
    Compute bill dates for a contract.

    Rules:
    - first scheduled date = start_date
    - each next date = previous + interval_months
    - include dates while date <= end_date
    - normalize to naive UTC for DB consistency
    """
    if interval_months <= 0:
        return []
    start_dt = _to_naive_utc(start_date)
    end_dt = _to_naive_utc(end_date)
    if start_dt > end_dt:
        return []

    dates: list[datetime] = []
    cur = start_dt
    while cur <= end_dt:
        dates.append(cur)
        cur = _add_months(cur, interval_months)
    return dates


class ContractService:
    """Contract service for managing contract data in database"""

    def __init__(self, session: AsyncSession):
        """Initialize the service with database session"""
        self._session = session

    async def get_by_id(self, contract_id: UUID) -> ContractRead | None:
        """
        Get a contract by ID

        Args:
            contract_id: The ID of the contract to retrieve

        Returns:
            ContractRead if found, None otherwise
        """
        # Validate contract_id before querying database
        if contract_id is None:
            return None

        statement = select(Contract).where(Contract.id == contract_id)
        result = await self._session.execute(statement)
        db_contract = result.scalar_one_or_none()
        if db_contract is None:
            return None
        return ContractRead.model_validate(db_contract)

    async def get_all(self, customer_id: UUID | None = None) -> list[ContractRead]:  # noqa: E501
        """
        Get all contracts, optionally filtered by customer_id

        Args:
            customer_id: Optional customer ID to filter contracts

        Returns:
            List of contracts
        """
        if customer_id is None:
            # Get all contracts
            statement = select(Contract)
        else:
            # Get contracts filtered by customer_id
            statement = select(Contract).where(Contract.customer_id == customer_id)  # noqa: E501

        result = await self._session.execute(statement)
        db_contracts = result.scalars().all()
        return [ContractRead.model_validate(contract) for contract in db_contracts]  # noqa: E501

    async def create(self, contract: ContractWrite) -> ContractRead | None:
        """
        Create a new contract

        Args:
            contract: Contract data to create

        Returns:
            Created contract with assigned ID,
            None if customer_id doesn't exist
        """
        if contract is None:
            return None

        # Verify customer_id exists before creating contract
        customer_statement = select(Customer).where(Customer.id == contract.customer_id)  # noqa: E501
        customer_result = await self._session.execute(customer_statement)
        db_customer = customer_result.scalar_one_or_none()
        if db_customer is None:
            logger.warning(
                f"Failed to create contract: customer_id "
                f"{contract.customer_id} does not exist"
            )
            return None

        # Create database model instance
        db_contract = Contract(
            customer_id=contract.customer_id,
            product_name=contract.product_name,
            start_date=contract.start_date,
            end_date=contract.end_date,
            monthly_rent=contract.monthly_rent,
            billing_interval=contract.billing_interval,
            notes=contract.notes,
            status=contract.status,
            contract_number=_generate_contract_number(),
            signed_date=contract.signed_date,
            payment_method=contract.payment_method,
            next_billing_date=contract.next_billing_date,
            invoice_type=contract.invoice_type,
            terminated_at=contract.terminated_at,
            termination_reason=contract.termination_reason,
        )

        # Add to session and commit
        self._session.add(db_contract)
        await self._session.commit()
        await self._session.refresh(db_contract)

        # Convert to read schema
        return ContractRead.model_validate(db_contract)

    async def delete(self, contract_id: UUID) -> bool:
        """
        Delete a contract by ID

        Args:
            contract_id: The ID of the contract to delete

        Returns:
            True if contract was deleted, False if contract not found
        """
        # Validate contract_id before querying database
        if contract_id is None:
            return False

        # Get contract first to check if it exists
        statement = select(Contract).where(Contract.id == contract_id)
        result = await self._session.execute(statement)
        db_contract = result.scalar_one_or_none()
        if db_contract is None:
            logger.warning(
                f"Failed to delete contract: contract_id {contract_id} does not exist"  # noqa: E501
            )
            return False

        # Delete the contract using delete statement
        delete_statement = delete(Contract).where(
            Contract.id == contract_id  # type: ignore[arg-type]
        )
        await self._session.execute(delete_statement)
        await self._session.commit()
        return True

    async def update(
        self, contract_id: UUID, contract_update: ContractUpdate
    ) -> ContractRead:
        """
        Update a contract by ID

        Args:
            contract_id: The ID of the contract to update
            contract_update: Contract data to update (partial update supported)

        Returns:
            ContractRead if contract was updated

        Raises:
            ValueError: If contract not found
        """
        # Validate contract_id before querying database
        if contract_id is None:
            raise ValueError("Contract ID cannot be None")

        # Get contract first to check if it exists
        statement = select(Contract).where(Contract.id == contract_id)
        result = await self._session.execute(statement)
        db_contract = result.scalar_one_or_none()
        if db_contract is None:
            logger.warning(
                f"Failed to update contract: contract_id {contract_id} does not exist"  # noqa: E501
            )
            raise ValueError(f"Contract with ID {contract_id} not found")

        # Update only provided fields
        update_data = contract_update.model_dump(exclude_unset=True)

        # When transitioning PENDING -> ACTIVE: create all bills and set next_billing_date # noqa: E501
        creating_bills = False
        if "status" in update_data and update_data["status"] == ContractStatus.ACTIVE:  # noqa: E501
            if db_contract.status in (ContractStatus.PENDING):
                creating_bills = True
                if "next_billing_date" not in update_data:
                    n = int(db_contract.billing_interval.value)
                    update_data["next_billing_date"] = _add_months(
                        db_contract.start_date, n
                    )

        # Normalize datetime fields to naive UTC so DB (TIMESTAMP WITHOUT TIME ZONE) accepts them # noqa: E501
        for key in _CONTRACT_TIMESTAMP_FIELDS:
            if key in update_data and isinstance(update_data[key], datetime):
                update_data[key] = _to_naive_utc(update_data[key])

        for field, value in update_data.items():
            setattr(db_contract, field, value)

        if creating_bills:
            # Prevent duplicate bill creation if status patch is repeated.
            existing_count_result = await self._session.execute(
                select(func.count())
                .select_from(Bill)
                .where(Bill.contract_id == db_contract.id)
            )
            existing_count = int(existing_count_result.scalar_one() or 0)
            if existing_count == 0:
                interval_months = int(db_contract.billing_interval.value)
                bill_dates = _compute_bill_dates(
                    db_contract.start_date,
                    db_contract.end_date,
                    interval_months,
                )
                await BillService(self._session).create_all_bills_for_contract(
                    db_contract,
                    bill_dates=bill_dates,
                )

        # Commit the changes
        await self._session.commit()
        await self._session.refresh(db_contract)

        # Convert to read schema
        return ContractRead.model_validate(db_contract)
