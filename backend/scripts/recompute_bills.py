"""Recompute amounts of auto-generated DRAFT bills (quantity = months billed).

Bills created before the fix had quantity 1, so a 12-month interval was billed as one month.

Usage (from backend/):
    python -m scripts.recompute_bills           # dry run
    python -m scripts.recompute_bills --apply   # write to DB

Only bills that still look auto-generated are changed: status DRAFT, exactly one item with
quantity 1 and unit_price == contract.monthly_rent, and the contract's bills match its periods
(same count, same start dates). Everything else is listed, never touched.
"""

import argparse
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import select

from app.api.schemas.bill import BillStatus
from app.database.models.bill import Bill
from app.database.models.contract import Contract
from app.database.session import engine
from app.services.bill_service import BillService
from app.services.contract_service import _compute_bill_periods


async def fix_contract_bills(
    session: AsyncSession, contract: Contract
) -> tuple[list[str], list[str]]:
    """Return (fixed bill numbers, skip reasons). Does not commit."""
    bills = list(
        (
            await session.execute(
                select(Bill)
                .where(Bill.contract_id == contract.id)
                .order_by(Bill.created_at)  # type: ignore[arg-type]
            )
        ).scalars()
    )
    periods = _compute_bill_periods(
        contract.start_date, contract.end_date, int(contract.billing_interval.value)
    )
    if len(bills) != len(periods) or any(
        b.created_at != p[0] for b, p in zip(bills, periods, strict=True)
    ):
        return [], [f"{contract.contract_number}: bills do not match contract periods"]

    calc = BillService(session)._calculate_amounts_from_items
    unit_price = float(contract.monthly_rent)
    fixed: list[str] = []
    skipped: list[str] = []
    for bill, (_, months) in zip(bills, periods, strict=True):
        items = bill.items or []
        quantity = float(months)
        one_item = (
            len(items) == 1 and float(items[0].get("unit_price", -1)) == unit_price
        )
        if one_item and float(items[0].get("quantity", 0)) == quantity:
            continue  # already correct
        if bill.status != BillStatus.DRAFT:
            skipped.append(f"{bill.bill_number}: {bill.status}, not changed")
        elif not one_item or float(items[0].get("quantity", 0)) != 1.0:
            skipped.append(f"{bill.bill_number}: items edited by hand, not changed")
        else:
            tax, amount = calc(
                [{"quantity": quantity, "unit_price": unit_price}], bill.invoice_type
            )
            bill.items = [
                {
                    **items[0],
                    "quantity": quantity,
                    "amount": round(quantity * unit_price, 2),
                }
            ]
            bill.amount = amount
            bill.tax_amount = tax
            fixed.append(bill.bill_number)
    return fixed, skipped


async def main(apply: bool) -> None:
    factory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        contracts = (await session.execute(select(Contract))).scalars().all()
        total_fixed = 0
        for contract in contracts:
            fixed, skipped = await fix_contract_bills(session, contract)
            total_fixed += len(fixed)
            for bn in fixed:
                print(f"fix   {bn}")
            for msg in skipped:
                print(f"skip  {msg}")
        if apply:
            await session.commit()
            print(f"updated {total_fixed} bills")
        else:
            await session.rollback()
            print(f"dry run: {total_fixed} bills would change (use --apply)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    asyncio.run(main(ap.parse_args().apply))
