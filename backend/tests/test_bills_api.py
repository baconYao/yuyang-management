import re
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import delete

from app.database.models.bill import Bill
from app.database.models.contract import Contract
from app.database.models.customer import Customer


BILL_NUMBER_PATTERN = re.compile(r"^B-\d{4}-\d{2}-[A-Z]{5}$")


@pytest.mark.asyncio
async def test_pending_to_active_creates_all_bills(
    client: AsyncClient, test_session
):
    """
    When a contract transitions PENDING -> ACTIVE, the system should create all bills
    across the contract period, with status DRAFT and created_at aligned to bill dates.
    """
    await test_session.execute(delete(Bill))
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()

    cust = Customer(
        customer_name="Bill API Customer",
        invoice_title="Bill API Invoice",
        invoice_number="BILLAPI001",
        contact_phone="0900000000",
        messaging_app_line="bill_api_line",
        address="Bill API Address",
        primary_contact="Bill API Contact",
        customer_type="COMPANY",
    )
    test_session.add(cust)
    await test_session.commit()
    await test_session.refresh(cust)

    start_date = datetime(2026, 1, 1, 0, 0, 0)
    end_date = datetime(2026, 12, 31, 0, 0, 0)

    contract_payload = {
        "customer_id": str(cust.id),
        "product_name": "Bill Product",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "monthly_rent": 10000,
        "billing_interval": "3",
        "status": "PENDING",
    }
    create_resp = await client.post(
        "/api/v1/contracts/", json=contract_payload
    )
    assert create_resp.status_code == 201
    contract = create_resp.json()
    contract_id = contract["id"]

    patch_resp = await client.patch(
        f"/api/v1/contracts/{contract_id}",
        json={"status": "ACTIVE"},
    )
    assert patch_resp.status_code == 200

    bills_resp = await client.get(
        "/api/v1/bills/",
        params={"contract_id": contract_id},
    )
    assert bills_resp.status_code == 200
    bills = bills_resp.json()

    # Expect 4 bills: 2026-01-01, 04-01, 07-01, 10-01
    assert len(bills) == 4
    created_dates = sorted([(b["created_at"] or "")[:10] for b in bills])
    assert created_dates == [
        "2026-01-01",
        "2026-04-01",
        "2026-07-01",
        "2026-10-01",
    ]

    for b in bills:
        assert BILL_NUMBER_PATTERN.match(b["bill_number"])
        assert b["status"] == "DRAFT"


@pytest.mark.asyncio
async def test_get_bills_within_days_prefers_due_date_else_created_at(
    client: AsyncClient, test_session
):
    """
    within_days filters on COALESCE(due_date, created_at) between now and now+N days.
    """
    await test_session.execute(delete(Bill))
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()

    cust = Customer(
        customer_name="Horizon Customer",
        invoice_title="Horizon Invoice",
        invoice_number="HORIZON001",
        contact_phone="0912345678",
        messaging_app_line="horizon_line",
        address="Horizon Address",
        primary_contact="Horizon Contact",
        customer_type="COMPANY",
    )
    test_session.add(cust)
    await test_session.commit()
    await test_session.refresh(cust)

    now = datetime.utcnow()
    start_date = now - timedelta(days=30)
    end_date = now + timedelta(days=365)

    contract_payload = {
        "customer_id": str(cust.id),
        "product_name": "Horizon Product",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "monthly_rent": 10000,
        "billing_interval": "3",
        "status": "PENDING",
    }
    create_resp = await client.post(
        "/api/v1/contracts/", json=contract_payload
    )
    assert create_resp.status_code == 201
    contract_id = create_resp.json()["id"]
    patch_resp = await client.patch(
        f"/api/v1/contracts/{contract_id}",
        json={"status": "ACTIVE"},
    )
    assert patch_resp.status_code == 200

    bills_resp = await client.get(
        "/api/v1/bills/",
        params={"contract_id": contract_id},
    )
    assert bills_resp.status_code == 200
    bills = bills_resp.json()
    assert len(bills) >= 1

    # Pick one bill and set due_date in horizon.
    bill_to_due = bills[0]["bill_number"]
    due_date = (now + timedelta(days=2)).replace(microsecond=0)
    upd1 = await client.patch(
        f"/api/v1/bills/{bill_to_due}",
        json={"status": "DRAFT", "due_date": due_date.isoformat()},
    )
    assert upd1.status_code == 200

    # Create a manual bill whose created_at is used (due_date None), and put it in horizon.
    manual_bill_payload = {
        "customer_id": str(cust.id),
        "contract_id": contract_id,
        "amount": 100.0,
        "tax_amount": 0.0,
        "invoice_type": "NO_INVOICE",
        "status": "DRAFT",
        "notes": "",
        "items": [],
    }
    created_manual = await client.post(
        "/api/v1/bills/", json=manual_bill_payload
    )
    assert created_manual.status_code == 201
    manual_bill_number = created_manual.json()["bill_number"]

    # API doesn't expose created_at update, so we rely on \"just created\".
    # Add one more manual bill and move its due_date out of horizon to ensure it's excluded.
    out_bill_payload = dict(manual_bill_payload)
    created_out = await client.post("/api/v1/bills/", json=out_bill_payload)
    assert created_out.status_code == 201
    out_bill_number = created_out.json()["bill_number"]
    out_due = (now + timedelta(days=30)).replace(microsecond=0)
    upd2 = await client.patch(
        f"/api/v1/bills/{out_bill_number}",
        json={"status": "DRAFT", "due_date": out_due.isoformat()},
    )
    assert upd2.status_code == 200

    horizon_resp = await client.get(
        "/api/v1/bills/", params={"within_days": 7}
    )
    assert horizon_resp.status_code == 200
    horizon_bills = horizon_resp.json()
    horizon_numbers = {b["bill_number"] for b in horizon_bills}

    assert bill_to_due in horizon_numbers  # due_date inside
    assert manual_bill_number in horizon_numbers  # created_at fallback inside
    assert out_bill_number not in horizon_numbers  # due_date outside
