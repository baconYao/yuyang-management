import pytest
import pytest_asyncio
from sqlalchemy import delete

from app.api.schemas.customer import CustomerType
from app.database.models.customer import Customer
from app.services.customer_service import CustomerService


@pytest_asyncio.fixture(scope="function")
async def customer_service(test_session):
    """
    Create CustomerService instance
    """
    return CustomerService(test_session)


@pytest_asyncio.fixture(scope="function")
async def sample_customers(test_session):
    """
    Create test customer data
    """
    customers = [
        Customer(
            customer_name="測試客戶1",
            invoice_title="測試發票抬頭1",
            invoice_number="INV001",
            contact_phone="0912345678",
            messaging_app_line="line_id_1",
            address="台北市信義區",
            primary_contact="張三",
            customer_type=CustomerType.COMPANY,
        ),
        Customer(
            customer_name="測試客戶2",
            invoice_title="測試發票抬頭2",
            invoice_number="INV002",
            contact_phone="0923456789",
            messaging_app_line="line_id_2",
            address="新北市板橋區",
            primary_contact="李四",
            customer_type=CustomerType.REAL_ESTATE,
        ),
        Customer(
            customer_name="測試客戶3",
            invoice_title="測試發票抬頭3",
            invoice_number="INV003",
            contact_phone="0934567890",
            messaging_app_line="line_id_3",
            address="桃園市中壢區",
            primary_contact="王五",
            customer_type=CustomerType.EDUCATION,
        ),
    ]

    for customer in customers:
        test_session.add(customer)

    await test_session.commit()

    # Refresh to get generated IDs
    for customer in customers:
        await test_session.refresh(customer)

    yield customers

    # Clean up data after test to avoid affecting other tests
    await test_session.execute(delete(Customer))
    await test_session.commit()


@pytest.mark.asyncio
async def test_get_all_empty(customer_service, test_session):
    """
    Test get_all() returns empty list when database is empty
    """
    # Ensure database is empty
    await test_session.execute(delete(Customer))
    await test_session.commit()

    result = await customer_service.get_all()

    assert result == []
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_get_all_with_customers(customer_service, sample_customers):
    """
    Test get_all() returns all customer data
    """
    result = await customer_service.get_all()

    # Verify returned count
    assert len(result) == 3

    # Verify each customer's data
    assert all(customer.id is not None for customer in result)
    assert all(customer.customer_name is not None for customer in result)

    # Verify customer names
    customer_names = [customer.customer_name for customer in result]
    assert "測試客戶1" in customer_names
    assert "測試客戶2" in customer_names
    assert "測試客戶3" in customer_names

    # Verify customer types
    customer_types = [customer.customer_type for customer in result]
    assert CustomerType.COMPANY in customer_types
    assert CustomerType.REAL_ESTATE in customer_types
    assert CustomerType.EDUCATION in customer_types

    # Verify all fields have values
    for customer in result:
        assert customer.invoice_title is not None
        assert customer.invoice_number is not None
        assert customer.contact_phone is not None
        assert customer.messaging_app_line is not None
        assert customer.address is not None
        assert customer.primary_contact is not None
        assert customer.customer_type is not None
