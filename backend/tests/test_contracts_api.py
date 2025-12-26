# flake8: noqa: E501

from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select

from app.api.schemas.customer import CustomerType
from app.database.models.contract import Contract
from app.database.models.customer import Customer


@pytest.mark.asyncio
async def test_create_contract_via_api(client: AsyncClient, test_session):
    """
    Test POST /api/v1/contracts/ creates a contract in the test database
    """
    # Ensure database is empty
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()

    # Create a customer first
    test_customer = Customer(
        customer_name="API Test Customer",
        invoice_title="API Test Invoice",
        invoice_number="API001",
        contact_phone="0911111111",
        messaging_app_line="api_test_line",
        address="Test Address",
        primary_contact="Test Contact",
        customer_type=CustomerType.COMPANY,
    )
    test_session.add(test_customer)
    await test_session.commit()
    await test_session.refresh(test_customer)

    # Create contract via API
    start_date = datetime.now()
    end_date = start_date + timedelta(days=365)

    contract_data = {
        "customer_id": str(test_customer.id),
        "product_name": "API Test Product",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "monthly_rent": 15000,
        "billing_interval": "3",
        "notes": "API Test Notes",
        "status": "ACTIVE",
        "contract_number": "API-CONTRACT-001",
        "signed_date": (start_date - timedelta(days=1)).isoformat(),
        "payment_method": "BANK_TRANSFER",
        "next_billing_date": (start_date + timedelta(days=90)).isoformat(),
    }

    response = await client.post("/api/v1/contracts/", json=contract_data)
    assert response.status_code == 201
    created_contract = response.json()

    # Verify response
    assert created_contract["product_name"] == "API Test Product"
    assert created_contract["monthly_rent"] == 15000
    assert created_contract["billing_interval"] == "3"
    assert created_contract["notes"] == "API Test Notes"
    assert created_contract["status"] == "ACTIVE"
    assert created_contract["contract_number"] == "API-CONTRACT-001"
    assert created_contract["payment_method"] == "BANK_TRANSFER"
    assert created_contract["id"] is not None
    assert created_contract["customer_id"] == str(test_customer.id)
    assert created_contract["created_at"] is not None
    assert created_contract["updated_at"] is not None

    # Verify contract exists in test database
    contract_id = UUID(created_contract["id"])
    result = await test_session.execute(
        select(Contract).where(Contract.id == contract_id)  # type: ignore[arg-type]
    )
    db_contract = result.scalar_one_or_none()
    assert db_contract is not None
    assert db_contract.product_name == "API Test Product"
    assert db_contract.monthly_rent == 15000
    assert db_contract.customer_id == test_customer.id

    # Cleanup
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_contract_with_minimal_fields(client: AsyncClient, test_session):
    """
    Test POST /api/v1/contracts/ creates a contract with only required fields
    """
    # Ensure database is empty
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()

    # Create a customer first
    test_customer = Customer(
        customer_name="Minimal Test Customer",
        invoice_title="Minimal Invoice",
        invoice_number="MIN001",
        contact_phone="0922222222",
        messaging_app_line="minimal_line",
        address="Minimal Address",
        primary_contact="Minimal Contact",
        customer_type=CustomerType.EDUCATION,
    )
    test_session.add(test_customer)
    await test_session.commit()
    await test_session.refresh(test_customer)

    # Create contract with minimal fields via API
    start_date = datetime.now()
    end_date = start_date + timedelta(days=365)

    contract_data = {
        "customer_id": str(test_customer.id),
        "product_name": "Minimal Product",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "monthly_rent": 5000,
        "billing_interval": "6",
        "status": "PENDING",
    }

    response = await client.post("/api/v1/contracts/", json=contract_data)
    assert response.status_code == 201
    created_contract = response.json()

    # Verify response
    assert created_contract["product_name"] == "Minimal Product"
    assert created_contract["monthly_rent"] == 5000
    assert created_contract["billing_interval"] == "6"
    assert created_contract["status"] == "PENDING"
    assert created_contract["notes"] is None
    assert created_contract["contract_number"] is None
    assert created_contract["signed_date"] is None
    assert created_contract["payment_method"] is None
    assert created_contract["next_billing_date"] is None
    assert created_contract["terminated_at"] is None
    assert created_contract["termination_reason"] is None

    # Cleanup
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_contract_missing_required_fields(client: AsyncClient):
    """
    Test POST /api/v1/contracts/ returns 422 when required fields are missing
    """
    # Try to create contract without required fields
    contract_data = {
        "product_name": "Incomplete Product",
        # Missing customer_id, start_date, end_date, monthly_rent, etc.
    }

    response = await client.post("/api/v1/contracts/", json=contract_data)
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail


@pytest.mark.asyncio
async def test_create_contract_invalid_customer_id(client: AsyncClient):
    """
    Test POST /api/v1/contracts/ returns error for invalid customer_id
    """
    start_date = datetime.now()
    end_date = start_date + timedelta(days=365)

    contract_data = {
        "customer_id": str(uuid4()),  # Non-existent customer ID
        "product_name": "Test Product",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "monthly_rent": 10000,
        "billing_interval": "12",
        "status": "ACTIVE",
    }

    response = await client.post("/api/v1/contracts/", json=contract_data)
    # Should return error (422 or 400) due to foreign key constraint
    assert response.status_code in [400, 422, 500]
    error_detail = response.json()
    assert "detail" in error_detail


@pytest.mark.asyncio
async def test_create_contract_invalid_billing_interval(
    client: AsyncClient, test_session
):
    """
    Test POST /api/v1/contracts/ returns 422 for invalid billing_interval
    """
    # Ensure database is empty
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()

    # Create a customer first
    test_customer = Customer(
        customer_name="Invalid Test Customer",
        invoice_title="Invalid Invoice",
        invoice_number="INV001",
        contact_phone="0933333333",
        messaging_app_line="invalid_line",
        address="Invalid Address",
        primary_contact="Invalid Contact",
        customer_type=CustomerType.COMPANY,
    )
    test_session.add(test_customer)
    await test_session.commit()
    await test_session.refresh(test_customer)

    start_date = datetime.now()
    end_date = start_date + timedelta(days=365)

    contract_data = {
        "customer_id": str(test_customer.id),
        "product_name": "Test Product",
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "monthly_rent": 10000,
        "billing_interval": "99",  # Invalid billing interval
        "status": "ACTIVE",
    }

    response = await client.post("/api/v1/contracts/", json=contract_data)
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail

    # Cleanup
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_contract_product_name_too_long(client: AsyncClient, test_session):
    """
    Test POST /api/v1/contracts/ returns 422 when product_name exceeds 30 characters
    """
    # Ensure database is empty
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()

    # Create a customer first
    test_customer = Customer(
        customer_name="Long Name Test Customer",
        invoice_title="Long Name Invoice",
        invoice_number="LONG001",
        contact_phone="0944444444",
        messaging_app_line="long_name_line",
        address="Long Name Address",
        primary_contact="Long Name Contact",
        customer_type=CustomerType.COMPANY,
    )
    test_session.add(test_customer)
    await test_session.commit()
    await test_session.refresh(test_customer)

    start_date = datetime.now()
    end_date = start_date + timedelta(days=365)

    contract_data = {
        "customer_id": str(test_customer.id),
        "product_name": "A" * 31,  # 31 characters, exceeds max of 30
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "monthly_rent": 10000,
        "billing_interval": "12",
        "status": "ACTIVE",
    }

    response = await client.post("/api/v1/contracts/", json=contract_data)
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail

    # Cleanup
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()
