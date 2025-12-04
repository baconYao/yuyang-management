from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select

from app.api.schemas.customer import CustomerType
from app.database.models.customer import Customer


@pytest.mark.asyncio
async def test_get_customers_empty(client: AsyncClient, test_session):
    """
    Test GET /api/v1/customers/ returns empty list when database is empty
    This verifies that the API endpoint uses the test database.
    """
    # Ensure database is empty
    await test_session.execute(delete(Customer))
    await test_session.commit()

    response = await client.get("/api/v1/customers/")
    assert response.status_code == 200
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_create_customer_via_api(client: AsyncClient, test_session):
    """
    Test POST /api/v1/customers/ creates a customer in the test database
    This verifies that the API endpoint uses the test database, not production.
    """
    # Ensure database is empty
    await test_session.execute(delete(Customer))
    await test_session.commit()

    # Create customer via API
    customer_data = {
        "customer_name": "API Test Customer",
        "invoice_title": "API Test Invoice",
        "invoice_number": "API001",
        "contact_phone": "0911111111",
        "messaging_app_line": "api_test_line",
        "address": "Test Address",
        "primary_contact": "Test Contact",
        "customer_type": "COMPANY",
    }

    response = await client.post("/api/v1/customers/", json=customer_data)
    assert response.status_code == 201
    created_customer = response.json()

    # Verify response
    assert created_customer["customer_name"] == "API Test Customer"
    assert created_customer["invoice_number"] == "API001"
    assert created_customer["id"] is not None

    # Verify customer exists in test database
    # Convert string ID to UUID object
    customer_id = UUID(created_customer["id"])
    result = await test_session.execute(
        select(Customer).where(
            Customer.id == customer_id  # type: ignore[arg-type]
        )
    )
    db_customer = result.scalar_one_or_none()
    assert db_customer is not None
    assert db_customer.customer_name == "API Test Customer"
    assert db_customer.invoice_number == "API001"

    # Cleanup
    await test_session.execute(delete(Customer))
    await test_session.commit()


@pytest.mark.asyncio
async def test_get_customers_with_data(client: AsyncClient, test_session):
    """
    Test GET /api/v1/customers/ returns customers from test database
    """
    # Ensure database is empty
    await test_session.execute(delete(Customer))
    await test_session.commit()

    # Create test customer directly in test database
    test_customer = Customer(
        customer_name="Direct DB Customer",
        invoice_title="Direct DB Invoice",
        invoice_number="DB001",
        contact_phone="0922222222",
        messaging_app_line="db_test_line",
        address="DB Test Address",
        primary_contact="DB Contact",
        customer_type=CustomerType.EDUCATION,
    )
    test_session.add(test_customer)
    await test_session.commit()
    await test_session.refresh(test_customer)

    # Get customers via API
    response = await client.get("/api/v1/customers/")
    assert response.status_code == 200
    customers = response.json()

    # Verify API returns the customer we created directly in test DB
    assert len(customers) == 1
    assert customers[0]["customer_name"] == "Direct DB Customer"
    assert customers[0]["invoice_number"] == "DB001"
    assert customers[0]["id"] == str(test_customer.id)

    # Cleanup
    await test_session.execute(delete(Customer))
    await test_session.commit()


@pytest.mark.asyncio
async def test_get_customer_by_id_success(client: AsyncClient, test_session):
    """
    Test GET /api/v1/customers/{customer_id} returns customer when found
    """
    # Ensure database is empty
    await test_session.execute(delete(Customer))
    await test_session.commit()

    # Create test customer directly in test database
    test_customer = Customer(
        customer_name="Test Customer for ID",
        invoice_title="Test Invoice Title",
        invoice_number="ID001",
        contact_phone="0933333333",
        messaging_app_line="id_test_line",
        address="ID Test Address",
        primary_contact="ID Contact",
        customer_type=CustomerType.COMPANY,
    )
    test_session.add(test_customer)
    await test_session.commit()
    await test_session.refresh(test_customer)

    # Get customer by ID via API
    customer_id = str(test_customer.id)
    response = await client.get(f"/api/v1/customers/{customer_id}")
    assert response.status_code == 200
    customer = response.json()

    # Verify response data
    assert customer["id"] == customer_id
    assert customer["customer_name"] == "Test Customer for ID"
    assert customer["invoice_title"] == "Test Invoice Title"
    assert customer["invoice_number"] == "ID001"
    assert customer["contact_phone"] == "0933333333"
    assert customer["messaging_app_line"] == "id_test_line"
    assert customer["address"] == "ID Test Address"
    assert customer["primary_contact"] == "ID Contact"
    assert customer["customer_type"] == "COMPANY"

    # Cleanup
    await test_session.execute(delete(Customer))
    await test_session.commit()


@pytest.mark.asyncio
async def test_get_customer_by_id_not_found(client: AsyncClient, test_session):
    """
    Test GET /api/v1/customers/{customer_id} returns 404
    when customer not found
    """
    # Ensure database is empty
    await test_session.execute(delete(Customer))
    await test_session.commit()

    # Try to get non-existent customer
    non_existent_id = str(uuid4())
    response = await client.get(f"/api/v1/customers/{non_existent_id}")
    assert response.status_code == 404
    error_detail = response.json()
    assert "detail" in error_detail
    assert non_existent_id in error_detail["detail"]
    assert "not found" in error_detail["detail"].lower()


@pytest.mark.asyncio
async def test_get_customer_by_id_invalid_uuid(client: AsyncClient):
    """
    Test GET /api/v1/customers/{customer_id} returns 422
    for invalid UUID format
    """
    # Try to get customer with invalid UUID format
    invalid_id = "not-a-valid-uuid"
    response = await client.get(f"/api/v1/customers/{invalid_id}")
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail
