import logging
import random
import string
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import func
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

    def _calculate_amounts_from_items(
        self, items: list[dict], invoice_type: InvoiceType | None
    ) -> tuple[float, float]:
        """
        Calculate (tax_amount, total_amount) from bill items.

        - subtotal is sum(quantity * unit_price) across items
        - tax is 5% only for TRIPLE_UNIFORM_INVOICE
        """
        subtotal = 0.0
        for d in items or []:
            if not isinstance(d, dict):
                continue
            try:
                qty = float(d.get("quantity", 0) or 0)
                up = float(d.get("unit_price", 0) or 0)
                if qty < 0 or up < 0:
                    continue
                subtotal += qty * up
            except (TypeError, ValueError):
                continue
        tax_amount = 0.0
        if invoice_type == InvoiceType.TRIPLE_UNIFORM_INVOICE:
            tax_amount = round(subtotal * 0.05, 2)
        total = round(subtotal + tax_amount, 2)
        return (tax_amount, total)

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
        within_days: int | None = None,
    ) -> list[BillRead]:
        """
        Get all bills, optionally filtered by customer_id, contract_id, or statuses. # noqa: E501

        Args:
            customer_id: Optional customer ID to filter bills
            contract_id: Optional contract ID to filter bills
            statuses: Optional list of BillStatus to filter bills (e.g. [DRAFT], [PAID, OVERDUE, CANCELLED])
            within_days: If set, only return bills whose reference date is within next N days.
                        Reference date = COALESCE(due_date, created_at).

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
        if within_days is not None:
            if within_days < 0:
                within_days = 0
            now = datetime.utcnow()
            until = now + timedelta(days=int(within_days))
            ref_date = func.coalesce(Bill.due_date, Bill.created_at)
            # Include all past bills and future bills up to now + N days.
            statement = statement.where(ref_date < until)
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

        items_json: list[dict] = []
        if bill.items:
            for i, item in enumerate(bill.items):
                try:
                    qty = float(item.quantity)
                except (TypeError, ValueError):
                    qty = 0.0
                try:
                    up = float(item.unit_price)
                except (TypeError, ValueError):
                    up = 0.0
                items_json.append(
                    {
                        "product_name": item.product_name or "",
                        "quantity": qty,
                        "unit_price": up,
                        "amount": round(qty * up, 2),
                        "sort_order": getattr(item, "sort_order", i),
                    }
                )

        # Ensure amount/tax_amount are consistent with items.
        tax_amount, amount = self._calculate_amounts_from_items(
            items_json,
            bill.invoice_type,
        )

        db_bill = Bill(
            bill_number=_generate_bill_number(),
            customer_id=bill.customer_id,
            contract_id=bill.contract_id,
            amount=amount,
            tax_amount=tax_amount,
            invoice_type=bill.invoice_type,
            status=bill.status,
            notes=bill.notes or "",
            previous_bill_number=previous_bill_number,
            items=items_json,
        )
        self._session.add(db_bill)
        await self._session.commit()
        await self._session.refresh(db_bill)
        return self._bill_to_read(db_bill)

    def create_first_bill_for_contract(self, db_contract: Contract) -> None:
        """
        Build and add the first bill for a contract (e.g. when status becomes ACTIVE). # noqa: E501
        Does not commit; caller must commit to keep same transaction.
        First bill's created_at/updated_at = contract start_date (帳單起始日期).
        """
        interval_months = int(db_contract.billing_interval.value)
        invoice_type = (
            db_contract.invoice_type
            if db_contract.invoice_type is not None
            else InvoiceType.NO_INVOICE
        )
        unit_price = float(db_contract.monthly_rent)
        subtotal = unit_price * interval_months
        tax_amount, amount = self._calculate_amounts_from_items(
            [
                {
                    "quantity": float(interval_months),
                    "unit_price": unit_price,
                }
            ],
            invoice_type,
        )
        items_json = [
            {
                "product_name": db_contract.product_name or "",
                "quantity": float(interval_months),
                "unit_price": unit_price,
                "amount": round(subtotal, 2),
                "sort_order": 0,
            }
        ]
        # 第一筆帳單的起始日期 = 合約起始日（前端顯示為 created_at）
        start_dt = db_contract.start_date
        if getattr(start_dt, "tzinfo", None) is not None:
            start_dt = start_dt.astimezone(UTC).replace(tzinfo=None)
        db_bill = Bill(
            bill_number=_generate_bill_number(),
            customer_id=db_contract.customer_id,
            contract_id=db_contract.id,
            amount=amount,
            tax_amount=tax_amount,
            invoice_type=invoice_type,
            status=BillStatus.DRAFT,
            notes="",
            previous_bill_number=None,
            items=items_json,
            created_at=start_dt,
            updated_at=start_dt,
        )
        self._session.add(db_bill)

    def create_bills_for_contract(
        self,
        db_contract: Contract,
        bill_dates: list[datetime],
    ) -> None:
        """
        Build and add all bills for a contract (e.g. when status becomes ACTIVE).
        Does not commit; caller must commit to keep same transaction.

        - status: DRAFT
        - bill date is stored in created_at/updated_at (front-end uses created_at)
        - amount/tax/items follow the same model as create_first_bill_for_contract
        - previous_bill_number is chained in creation order
        """
        if not bill_dates:
            return

        interval_months = int(db_contract.billing_interval.value)
        invoice_type = (
            db_contract.invoice_type
            if db_contract.invoice_type is not None
            else InvoiceType.NO_INVOICE
        )
        unit_price = float(db_contract.monthly_rent)
        subtotal = unit_price * interval_months
        tax_amount, amount = self._calculate_amounts_from_items(
            [
                {
                    "quantity": float(interval_months),
                    "unit_price": unit_price,
                }
            ],
            invoice_type,
        )
        items_json = [
            {
                "product_name": db_contract.product_name or "",
                "quantity": float(interval_months),
                "unit_price": unit_price,
                "amount": round(subtotal, 2),
                "sort_order": 0,
            }
        ]

        prev_bill_number: str | None = None
        for dt in bill_dates:
            # Normalize to naive UTC for DB.
            bill_dt = dt
            if getattr(bill_dt, "tzinfo", None) is not None:
                bill_dt = bill_dt.astimezone(UTC).replace(tzinfo=None)
            db_bill = Bill(
                bill_number=_generate_bill_number(),
                customer_id=db_contract.customer_id,
                contract_id=db_contract.id,
                amount=amount,
                tax_amount=tax_amount,
                invoice_type=invoice_type,
                status=BillStatus.DRAFT,
                notes="",
                previous_bill_number=prev_bill_number,
                items=items_json,
                created_at=bill_dt,
                updated_at=bill_dt,
            )
            self._session.add(db_bill)
            prev_bill_number = db_bill.bill_number

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
        invoice_type_in_payload = "invoice_type" in update_data

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
                try:
                    qty = float(item.get("quantity", 0) or 0)
                except (TypeError, ValueError):
                    qty = 0.0
                try:
                    up = float(item.get("unit_price", 0) or 0)
                except (TypeError, ValueError):
                    up = 0.0
                items_json.append(
                    {
                        "product_name": item.get("product_name") or "",
                        "quantity": qty,
                        "unit_price": up,
                        # Server-authoritative amount avoids stale client values.
                        "amount": round(qty * up, 2),
                        "sort_order": item.get("sort_order", sort_order),
                    }
                )
            db_bill.items = items_json
            tax_amount, amount = self._calculate_amounts_from_items(
                items_json,
                db_bill.invoice_type,
            )
            db_bill.tax_amount = tax_amount
            db_bill.amount = amount
        elif invoice_type_in_payload:
            # If invoice_type changes, recompute tax/amount from existing items.
            tax_amount, amount = self._calculate_amounts_from_items(
                getattr(db_bill, "items", []) or [],
                db_bill.invoice_type,
            )
            db_bill.tax_amount = tax_amount
            db_bill.amount = amount

        await self._session.commit()
        await self._session.refresh(db_bill)
        return self._bill_to_read(db_bill)
