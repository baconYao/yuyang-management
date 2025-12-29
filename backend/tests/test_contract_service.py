# flake8: noqa: E501

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import delete

from app.api.schemas.contract import (
    BillingInterval,
    ContractStatus,
    PaymentMethod,
)
from app.api.schemas.customer import CustomerType
from app.database.models.contract import Contract
from app.database.models.customer import Customer
from app.services.contract_service import ContractService


@pytest_asyncio.fixture(scope="function")
async def contract_service(test_session):
    """
    Create ContractService instance
    """
    return ContractService(test_session)


@pytest_asyncio.fixture(scope="function")
async def sample_customer(test_session):
    """
    Create a test customer for contract tests
    """
    customer = Customer(
        customer_name="測試客戶",
        invoice_title="測試發票抬頭",
        invoice_number="INV001",
        contact_phone="0912345678",
        messaging_app_line="line_id_1",
        address="台北市信義區",
        primary_contact="張三",
        customer_type=CustomerType.COMPANY,
    )
    test_session.add(customer)
    await test_session.commit()
    await test_session.refresh(customer)

    yield customer

    # Clean up
    await test_session.execute(delete(Customer))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_contract_success(contract_service, test_session, sample_customer):
    """
    Test create() successfully creates a contract
    """
    # Ensure database is empty
    await test_session.execute(delete(Contract))
    await test_session.commit()

    from app.api.schemas.contract import ContractWrite

    start_date = datetime.now()
    end_date = start_date + timedelta(days=365)

    contract_data = ContractWrite(
        customer_id=sample_customer.id,
        product_name="測試商品",
        start_date=start_date,
        end_date=end_date,
        monthly_rent=10000,
        billing_interval=BillingInterval.THREE_MONTHS,
        notes="測試備註",
        status=ContractStatus.ACTIVE,
        contract_number="CONTRACT-2024-001",
        signed_date=start_date - timedelta(days=1),
        payment_method=PaymentMethod.BANK_TRANSFER,
        next_billing_date=start_date + timedelta(days=90),
    )

    result = await contract_service.create(contract_data)

    # Verify result
    assert result is not None
    assert result.id is not None
    assert result.customer_id == sample_customer.id
    assert result.product_name == "測試商品"
    assert result.monthly_rent == 10000
    assert result.billing_interval == BillingInterval.THREE_MONTHS
    assert result.notes == "測試備註"
    assert result.status == ContractStatus.ACTIVE
    assert result.contract_number == "CONTRACT-2024-001"
    assert result.payment_method == PaymentMethod.BANK_TRANSFER
    assert result.created_at is not None
    assert result.updated_at is not None

    # Verify contract exists in database
    from sqlalchemy import select

    statement = select(Contract).where(Contract.id == result.id)
    db_result = await test_session.execute(statement)
    db_contract = db_result.scalar_one_or_none()
    assert db_contract is not None
    assert db_contract.product_name == "測試商品"
    assert db_contract.monthly_rent == 10000

    # Cleanup
    await test_session.execute(delete(Contract))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_contract_with_minimal_fields(
    contract_service, test_session, sample_customer
):
    """
    Test create() with only required fields
    """
    # Ensure database is empty
    await test_session.execute(delete(Contract))
    await test_session.commit()

    from app.api.schemas.contract import ContractWrite

    start_date = datetime.now()
    end_date = start_date + timedelta(days=365)

    contract_data = ContractWrite(
        customer_id=sample_customer.id,
        product_name="最小商品",
        start_date=start_date,
        end_date=end_date,
        monthly_rent=5000,
        billing_interval=BillingInterval.SIX_MONTHS,
        status=ContractStatus.PENDING,
    )

    result = await contract_service.create(contract_data)

    # Verify result
    assert result is not None
    assert result.id is not None
    assert result.customer_id == sample_customer.id
    assert result.product_name == "最小商品"
    assert result.monthly_rent == 5000
    assert result.billing_interval == BillingInterval.SIX_MONTHS
    assert result.status == ContractStatus.PENDING
    assert result.notes is None
    assert result.contract_number is None
    assert result.signed_date is None
    assert result.payment_method is None
    assert result.next_billing_date is None
    assert result.terminated_at is None
    assert result.termination_reason is None

    # Cleanup
    await test_session.execute(delete(Contract))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_contract_with_none_input(contract_service):
    """
    Test create() returns None when input is None
    """
    result = await contract_service.create(None)  # type: ignore[arg-type]
    assert result is None


@pytest.mark.asyncio
async def test_create_contract_invalid_customer_id(contract_service, test_session):
    """
    Test create() returns None when customer_id doesn't exist
    """
    # Ensure database is empty
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()

    from app.api.schemas.contract import ContractWrite

    start_date = datetime.now()
    end_date = start_date + timedelta(days=365)

    # Use a non-existent customer_id
    non_existent_customer_id = uuid4()

    contract_data = ContractWrite(
        customer_id=non_existent_customer_id,
        product_name="測試商品",
        start_date=start_date,
        end_date=end_date,
        monthly_rent=10000,
        billing_interval=BillingInterval.THREE_MONTHS,
        status=ContractStatus.ACTIVE,
    )

    result = await contract_service.create(contract_data)

    # Verify result is None when customer doesn't exist
    assert result is None

    # Verify no contract was created in database
    from sqlalchemy import select

    statement = select(Contract)
    db_result = await test_session.execute(statement)
    db_contracts = db_result.scalars().all()
    assert len(db_contracts) == 0

    # Cleanup
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()


@pytest.mark.asyncio
async def test_delete_contract_success(
    contract_service, test_session, sample_customer
):
    """
    Test delete() successfully deletes a contract
    """
    # Ensure database is empty
    await test_session.execute(delete(Contract))
    await test_session.commit()

    # Create a test contract
    from app.api.schemas.contract import ContractWrite

    start_date = datetime.now()
    end_date = start_date + timedelta(days=365)

    contract_data = ContractWrite(
        customer_id=sample_customer.id,
        product_name="Contract to Delete",
        start_date=start_date,
        end_date=end_date,
        monthly_rent=10000,
        billing_interval=BillingInterval.THREE_MONTHS,
        status=ContractStatus.ACTIVE,
    )

    created_contract = await contract_service.create(contract_data)
    assert created_contract is not None
    contract_id = created_contract.id

    # Verify contract exists before deletion
    from sqlalchemy import select

    statement = select(Contract).where(Contract.id == contract_id)
    db_result = await test_session.execute(statement)
    db_contract_before = db_result.scalar_one_or_none()
    assert db_contract_before is not None
    assert db_contract_before.product_name == "Contract to Delete"

    # Delete contract
    result = await contract_service.delete(contract_id)
    assert result is True

    # Verify contract no longer exists in database
    statement = select(Contract).where(Contract.id == contract_id)
    db_result = await test_session.execute(statement)
    db_contract_after = db_result.scalar_one_or_none()
    assert db_contract_after is None

    # Cleanup
    await test_session.execute(delete(Contract))
    await test_session.commit()


@pytest.mark.asyncio
async def test_delete_contract_not_found(contract_service, test_session):
    """
    Test delete() returns False when contract doesn't exist
    """
    # Ensure database is empty
    await test_session.execute(delete(Contract))
    await test_session.commit()

    # Try to delete non-existent contract
    non_existent_id = uuid4()
    result = await contract_service.delete(non_existent_id)

    # Verify result is False
    assert result is False

    # Cleanup
    await test_session.execute(delete(Contract))
    await test_session.commit()


@pytest.mark.asyncio
async def test_delete_contract_with_none_id(contract_service):
    """
    Test delete() returns False when contract_id is None
    """
    result = await contract_service.delete(None)  # type: ignore[arg-type]
    assert result is False
