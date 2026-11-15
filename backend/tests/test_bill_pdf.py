from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import delete

from app.database.models.bill import Bill
from app.database.models.contract import Contract
from app.database.models.customer import Customer


@pytest.mark.asyncio
async def test_pdf_tax_id_is_customer_tax_id_and_invoice_number_is_blank(
    client: AsyncClient, test_session, monkeypatch
):
    """統一編號 comes from the customer; 發票號碼 has no source yet and must stay blank."""
    captured: dict = {}

    def fake_generate(invoice_data: dict) -> bytes:
        captured.update(invoice_data)
        return b"%PDF-fake"

    monkeypatch.setattr("app.api.v1.bill.generate_pdf_bytes", fake_generate)

    await test_session.execute(delete(Bill))
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()
    cust = Customer(
        customer_name="Pdf Customer",
        invoice_title="t",
        invoice_number="12345678",  # 統一編號
        contact_phone="0900000000",
        messaging_app_line="l",
        address="a",
        primary_contact="p",
        customer_type="COMPANY",
    )
    test_session.add(cust)
    await test_session.commit()
    await test_session.refresh(cust)

    start = datetime(2026, 1, 1)
    contract = (
        await client.post(
            "/api/v1/contracts/",
            json={
                "customer_id": str(cust.id),
                "product_name": "Rent",
                "start_date": start.isoformat(),
                "end_date": datetime(2026, 12, 31).isoformat(),
                "monthly_rent": 2000,
                "billing_interval": "12",
                "status": "PENDING",
            },
        )
    ).json()
    await client.patch(f"/api/v1/contracts/{contract['id']}", json={"status": "ACTIVE"})
    (bill,) = (
        await client.get("/api/v1/bills/", params={"contract_id": contract["id"]})
    ).json()

    resp = await client.get(f"/api/v1/bills/{bill['bill_number']}/pdf")

    assert resp.status_code == 200
    assert captured["tax_id"] == "12345678"
    assert not captured.get("invoice_number")
