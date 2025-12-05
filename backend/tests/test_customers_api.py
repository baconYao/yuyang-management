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


@pytest.mark.asyncio
async def test_delete_customer_not_found(client: AsyncClient, test_session):
    """
    Test DELETE /api/v1/customers/{customer_id} returns 404
    when customer not found
    """
    # Ensure database is empty
    await test_session.execute(delete(Customer))
    await test_session.commit()

    # Try to delete non-existent customer
    non_existent_id = str(uuid4())
    response = await client.delete(f"/api/v1/customers/{non_existent_id}")
    assert response.status_code == 404
    error_detail = response.json()
    assert "detail" in error_detail
    assert non_existent_id in error_detail["detail"]
    assert "not found" in error_detail["detail"].lower()


@pytest.mark.asyncio
async def test_delete_customer_success(client: AsyncClient, test_session):
    """
    Test DELETE /api/v1/customers/{customer_id} successfully deletes
    an existing customer
    """
    # Ensure database is empty
    await test_session.execute(delete(Customer))
    await test_session.commit()

    # Create test customer directly in test database
    test_customer = Customer(
        customer_name="Customer to Delete",
        invoice_title="Delete Invoice Title",
        invoice_number="DEL001",
        contact_phone="0944444444",
        messaging_app_line="del_test_line",
        address="Delete Test Address",
        primary_contact="Delete Contact",
        customer_type=CustomerType.COMPANY,
    )
    test_session.add(test_customer)
    await test_session.commit()
    await test_session.refresh(test_customer)

    customer_id = str(test_customer.id)

    # Verify customer exists before deletion
    result = await test_session.execute(
        select(Customer).where(
            Customer.id == test_customer.id  # type: ignore[arg-type]
        )
    )
    db_customer_before = result.scalar_one_or_none()
    assert db_customer_before is not None
    assert db_customer_before.customer_name == "Customer to Delete"

    # Delete customer via API
    response = await client.delete(f"/api/v1/customers/{customer_id}")
    assert response.status_code == 204

    # Verify customer no longer exists in database
    result = await test_session.execute(
        select(Customer).where(
            Customer.id == test_customer.id  # type: ignore[arg-type]
        )
    )
    db_customer_after = result.scalar_one_or_none()
    assert db_customer_after is None

    # Cleanup (should be empty already, but just in case)
    await test_session.execute(delete(Customer))
    await test_session.commit()


@pytest.mark.asyncio
async def test_update_customer_not_found(client: AsyncClient, test_session):
    """
    Test PATCH /api/v1/customers/{customer_id} returns 404
    when customer not found
    """
    # Ensure database is empty
    await test_session.execute(delete(Customer))
    await test_session.commit()

    # Try to update non-existent customer
    non_existent_id = str(uuid4())
    update_data = {
        "customer_name": "Updated Name",
    }
    response = await client.patch(
        f"/api/v1/customers/{non_existent_id}", json=update_data
    )
    assert response.status_code == 404
    error_detail = response.json()
    assert "detail" in error_detail
    assert non_existent_id in error_detail["detail"]
    assert "not found" in error_detail["detail"].lower()


@pytest.mark.asyncio
async def test_update_customer_full_update(client: AsyncClient, test_session):
    """
    Test PATCH /api/v1/customers/{customer_id} successfully updates
    all fields of an existing customer
    """
    # Ensure database is empty
    await test_session.execute(delete(Customer))
    await test_session.commit()

    # Create test customer directly in test database
    test_customer = Customer(
        customer_name="Original Name",
        invoice_title="Original Invoice Title",
        invoice_number="ORIG001",
        contact_phone="0955555555",
        messaging_app_line="original_line",
        address="Original Address",
        primary_contact="Original Contact",
        customer_type=CustomerType.COMPANY,
    )
    test_session.add(test_customer)
    await test_session.commit()
    await test_session.refresh(test_customer)

    customer_id = str(test_customer.id)

    # Update all fields via API
    update_data = {
        "customer_name": "Updated Full Name",
        "invoice_title": "Updated Invoice Title",
        "invoice_number": "UPD001",
        "contact_phone": "0966666666",
        "messaging_app_line": "updated_line",
        "address": "Updated Address",
        "primary_contact": "Updated Contact",
        "customer_type": "EDUCATION",
    }

    response = await client.patch(f"/api/v1/customers/{customer_id}", json=update_data)  # noqa: E501
    assert response.status_code == 200
    updated_customer = response.json()

    # Verify response data
    assert updated_customer["id"] == customer_id
    assert updated_customer["customer_name"] == "Updated Full Name"
    assert updated_customer["invoice_title"] == "Updated Invoice Title"
    assert updated_customer["invoice_number"] == "UPD001"
    assert updated_customer["contact_phone"] == "0966666666"
    assert updated_customer["messaging_app_line"] == "updated_line"
    assert updated_customer["address"] == "Updated Address"
    assert updated_customer["primary_contact"] == "Updated Contact"
    assert updated_customer["customer_type"] == "EDUCATION"

    # Verify customer was updated in database
    # Remove the object from session to force fresh query from database
    test_session.expunge(test_customer)
    result = await test_session.execute(
        select(Customer).where(
            Customer.id == test_customer.id  # type: ignore[arg-type]
        )
    )
    db_customer = result.scalar_one_or_none()
    assert db_customer is not None
    assert db_customer.customer_name == "Updated Full Name"
    assert db_customer.invoice_title == "Updated Invoice Title"
    assert db_customer.invoice_number == "UPD001"
    assert db_customer.contact_phone == "0966666666"
    assert db_customer.messaging_app_line == "updated_line"
    assert db_customer.address == "Updated Address"
    assert db_customer.primary_contact == "Updated Contact"
    assert db_customer.customer_type == CustomerType.EDUCATION

    # Cleanup
    await test_session.execute(delete(Customer))
    await test_session.commit()


@pytest.mark.asyncio
async def test_update_customer_partial_update(client: AsyncClient, test_session):  # noqa: E501
    """
    Test PATCH /api/v1/customers/{customer_id} successfully updates
    only specified fields of an existing customer
    """
    # Ensure database is empty
    await test_session.execute(delete(Customer))
    await test_session.commit()

    # Create test customer directly in test database
    test_customer = Customer(
        customer_name="Original Name",
        invoice_title="Original Invoice Title",
        invoice_number="ORIG002",
        contact_phone="0977777777",
        messaging_app_line="original_line",
        address="Original Address",
        primary_contact="Original Contact",
        customer_type=CustomerType.REAL_ESTATE,
    )
    test_session.add(test_customer)
    await test_session.commit()
    await test_session.refresh(test_customer)

    customer_id = str(test_customer.id)
    original_invoice_number = test_customer.invoice_number
    original_contact_phone = test_customer.contact_phone
    original_customer_type = test_customer.customer_type

    # Update only some fields via API
    update_data = {
        "customer_name": "Partially Updated Name",
        "invoice_title": "Partially Updated Invoice Title",
        "address": "Partially Updated Address",
    }

    response = await client.patch(f"/api/v1/customers/{customer_id}", json=update_data)  # noqa: E501
    assert response.status_code == 200
    updated_customer = response.json()

    # Verify updated fields in response
    assert updated_customer["id"] == customer_id
    assert updated_customer["customer_name"] == "Partially Updated Name"
    assert updated_customer["invoice_title"] == "Partially Updated Invoice Title"  # noqa: E501
    assert updated_customer["address"] == "Partially Updated Address"

    # Verify unchanged fields in response
    assert updated_customer["invoice_number"] == original_invoice_number
    assert updated_customer["contact_phone"] == original_contact_phone
    assert updated_customer["customer_type"] == original_customer_type.value

    # Verify customer was partially updated in database
    # Remove the object from session to force fresh query from database
    test_session.expunge(test_customer)
    result = await test_session.execute(
        select(Customer).where(
            Customer.id == test_customer.id  # type: ignore[arg-type]
        )
    )
    db_customer = result.scalar_one_or_none()
    assert db_customer is not None
    assert db_customer.customer_name == "Partially Updated Name"
    assert db_customer.invoice_title == "Partially Updated Invoice Title"
    assert db_customer.address == "Partially Updated Address"
    # Verify unchanged fields
    assert db_customer.invoice_number == original_invoice_number
    assert db_customer.contact_phone == original_contact_phone
    assert db_customer.customer_type == original_customer_type

    # Cleanup
    await test_session.execute(delete(Customer))
    await test_session.commit()
