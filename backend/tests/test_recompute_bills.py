from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlmodel import select

from app.database.models.bill import Bill
from app.database.models.contract import Contract
from app.database.models.customer import Customer
from scripts.recompute_bills import fix_contract_bills


@pytest.mark.asyncio
async def test_recompute_fixes_old_draft_bills_only(client: AsyncClient, test_session):
    await test_session.execute(delete(Bill))
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()
    cust = Customer(
        customer_name="Recompute Customer",
        invoice_title="t",
        invoice_number="RECOMP001",
        contact_phone="0900000000",
        messaging_app_line="l",
        address="a",
        primary_contact="p",
        customer_type="COMPANY",
    )
    test_session.add(cust)
    await test_session.commit()
    await test_session.refresh(cust)

    resp = await client.post(
        "/api/v1/contracts/",
        json={
            "customer_id": str(cust.id),
            "product_name": "Rent",
            "start_date": datetime(2026, 11, 19).isoformat(),
            "end_date": datetime(2029, 11, 18).isoformat(),
            "monthly_rent": 2000,
            "billing_interval": "12",
            "status": "PENDING",
            "invoice_type": "TRIPLE_UNIFORM_INVOICE",
        },
    )
    contract_id = resp.json()["id"]
    await client.patch(f"/api/v1/contracts/{contract_id}", json={"status": "ACTIVE"})

    bills = list(
        (await test_session.execute(select(Bill).order_by(Bill.created_at))).scalars()  # type: ignore[arg-type]
    )
    assert len(bills) == 3
    # simulate the old bug on every bill: one month billed
    for b in bills:
        b.items = [{**b.items[0], "quantity": 1.0, "amount": 2000.0}]
        b.amount, b.tax_amount = 2100.0, 100.0
    bills[1].status = "SENT"  # already sent: must stay untouched
    await test_session.commit()

    contract = (await test_session.execute(select(Contract))).scalars().one()
    fixed, skipped = await fix_contract_bills(test_session, contract)
    await test_session.commit()

    assert fixed == [bills[0].bill_number, bills[2].bill_number]
    assert len(skipped) == 1 and bills[1].bill_number in skipped[0]
    for i in (0, 2):
        await test_session.refresh(bills[i])
        assert (bills[i].amount, bills[i].tax_amount) == (25200.0, 1200.0)
        assert bills[i].items[0]["quantity"] == 12.0
        assert bills[i].items[0]["amount"] == 24000.0
    await test_session.refresh(bills[1])
    assert bills[1].amount == 2100.0

    # second run is a no-op for the fixed ones
    fixed_again, _ = await fix_contract_bills(test_session, contract)
    assert fixed_again == []
