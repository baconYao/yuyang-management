from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlmodel import select

from app.database.models.bill import Bill
from app.database.models.contract import Contract
from app.database.models.customer import Customer
from app.services.contract_service import _add_months, _compute_bill_periods

INTERVALS = [1, 2, 3, 6, 12, 24, 36]
CONTRACT_MONTHS = [12, 24, 36]
STARTS = [datetime(2026, 11, 19), datetime(2026, 1, 31), datetime(2028, 2, 29)]


def _end(start: datetime, months: int) -> datetime:
    """Contract last day (inclusive): start + months - 1 day."""
    return _add_months(start, months) - timedelta(days=1)


def test_user_example_three_year_contract_yearly_bills():
    periods = _compute_bill_periods(datetime(2026, 11, 19), datetime(2029, 11, 18), 12)
    assert periods == [
        (datetime(2026, 11, 19), 12),
        (datetime(2027, 11, 19), 12),
        (datetime(2028, 11, 19), 12),
    ]


def test_month_end_start_does_not_drift():
    periods = _compute_bill_periods(
        datetime(2026, 1, 31), _end(datetime(2026, 1, 31), 12), 1
    )
    days = [(d.month, d.day) for d, _ in periods]
    assert days[:4] == [(1, 31), (2, 28), (3, 31), (4, 30)]
    assert days[-1] == (12, 31)


def test_last_bill_is_shorter_when_interval_does_not_divide_contract():
    periods = _compute_bill_periods(datetime(2026, 11, 19), datetime(2029, 11, 18), 24)
    assert periods == [(datetime(2026, 11, 19), 24), (datetime(2028, 11, 19), 12)]


@pytest.mark.parametrize("start", STARTS)
@pytest.mark.parametrize("months", CONTRACT_MONTHS)
@pytest.mark.parametrize("interval", INTERVALS)
def test_every_combination(start, months, interval):
    periods = _compute_bill_periods(start, _end(start, months), interval)

    assert len(periods) == -(-months // interval)  # ceil
    assert sum(m for _, m in periods) == months  # billed months == contract months
    assert periods[0][0] == start
    offset = 0
    for bill_start, billed in periods:
        assert bill_start == _add_months(start, offset)  # counted from start, no drift
        assert 1 <= billed <= interval
        offset += billed


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "interval, months, invoice_type, expected",
    [
        # (amount, tax) per bill, monthly_rent = 2000
        ("12", 36, "NO_INVOICE", [(24000.0, 0.0)] * 3),
        ("12", 36, "TRIPLE_UNIFORM_INVOICE", [(25200.0, 1200.0)] * 3),
        ("1", 12, "NO_INVOICE", [(2000.0, 0.0)] * 12),
        ("24", 48, "NO_INVOICE", [(48000.0, 0.0), (48000.0, 0.0)]),
    ],
)
async def test_activation_bills_months_times_rent(
    client: AsyncClient, test_session, interval, months, invoice_type, expected
):
    await test_session.execute(delete(Bill))
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()

    cust = Customer(
        customer_name="Period Customer",
        invoice_title="t",
        invoice_number="PERIOD001",
        contact_phone="0900000000",
        messaging_app_line="l",
        address="a",
        primary_contact="p",
        customer_type="COMPANY",
    )
    test_session.add(cust)
    await test_session.commit()
    await test_session.refresh(cust)

    start = datetime(2026, 11, 19)
    create_resp = await client.post(
        "/api/v1/contracts/",
        json={
            "customer_id": str(cust.id),
            "product_name": "Rent",
            "start_date": start.isoformat(),
            "end_date": _end(start, months).isoformat(),
            "monthly_rent": 2000,
            "billing_interval": interval,
            "status": "PENDING",
            "invoice_type": invoice_type,
        },
    )
    assert create_resp.status_code == 201
    contract_id = create_resp.json()["id"]
    patch_resp = await client.patch(
        f"/api/v1/contracts/{contract_id}", json={"status": "ACTIVE"}
    )
    assert patch_resp.status_code == 200

    bills = (
        await client.get("/api/v1/bills/", params={"contract_id": contract_id})
    ).json()
    bills.sort(key=lambda b: b["created_at"])

    assert [(b["amount"], b["tax_amount"]) for b in bills] == expected
    for b in bills:
        (item,) = b["items"]
        assert item["unit_price"] == 2000
        assert item["amount"] == item["quantity"] * 2000


async def _customer(test_session) -> Customer:
    await test_session.execute(delete(Bill))
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()
    cust = Customer(
        customer_name="Reject Customer",
        invoice_title="t",
        invoice_number="REJECT001",
        contact_phone="0900000000",
        messaging_app_line="l",
        address="a",
        primary_contact="p",
        customer_type="COMPANY",
    )
    test_session.add(cust)
    await test_session.commit()
    await test_session.refresh(cust)
    return cust


def _payload(cust, months: int, interval: str) -> dict:
    start = datetime(2026, 11, 19)
    return {
        "customer_id": str(cust.id),
        "product_name": "Rent",
        "start_date": start.isoformat(),
        "end_date": _end(start, months).isoformat(),
        "monthly_rent": 2000,
        "billing_interval": interval,
        "status": "PENDING",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "months, interval",
    [(36, "24"), (12, "24"), (12, "36"), (24, "36"), (30, "12"), (13, "3")],
)
async def test_create_rejects_term_not_divisible_by_interval(
    client: AsyncClient, test_session, months, interval
):
    cust = await _customer(test_session)
    resp = await client.post(
        "/api/v1/contracts/", json=_payload(cust, months, interval)
    )
    assert resp.status_code == 422
    assert f"{months} months" in resp.json()["detail"]
    assert (await test_session.execute(select(Contract))).first() is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "months, interval", [(36, "12"), (36, "36"), (24, "24"), (12, "1")]
)
async def test_create_accepts_divisible_term(
    client: AsyncClient, test_session, months, interval
):
    cust = await _customer(test_session)
    resp = await client.post(
        "/api/v1/contracts/", json=_payload(cust, months, interval)
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_update_rejects_interval_that_does_not_divide_term(
    client: AsyncClient, test_session
):
    cust = await _customer(test_session)
    created = await client.post("/api/v1/contracts/", json=_payload(cust, 36, "12"))
    contract_id = created.json()["id"]

    bad = await client.patch(
        f"/api/v1/contracts/{contract_id}", json={"billing_interval": "24"}
    )
    assert bad.status_code == 422
    ok = await client.patch(
        f"/api/v1/contracts/{contract_id}", json={"billing_interval": "6"}
    )
    assert ok.status_code == 200
    # unrelated edits never trigger the check
    notes = await client.patch(f"/api/v1/contracts/{contract_id}", json={"notes": "x"})
    assert notes.status_code == 200
