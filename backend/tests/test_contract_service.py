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
async def test_get_by_id_success(contract_service, test_session, sample_customer):
    """
    Test get_by_id() successfully retrieves a contract
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
        product_name="測試商品",
        start_date=start_date,
        end_date=end_date,
        monthly_rent=10000,
        billing_interval=BillingInterval.THREE_MONTHS,
        notes="測試備註",
        status=ContractStatus.ACTIVE,
        contract_number="CONTRACT-2024-001",
    )

    created_contract = await contract_service.create(contract_data)
    assert created_contract is not None
    contract_id = created_contract.id

    # Get contract by ID
    result = await contract_service.get_by_id(contract_id)

    # Verify result
    assert result is not None
    assert result.id == contract_id
    assert result.product_name == "測試商品"
    assert result.monthly_rent == 10000
    assert result.billing_interval == BillingInterval.THREE_MONTHS
    assert result.notes == "測試備註"
    assert result.status == ContractStatus.ACTIVE
    assert result.contract_number == "CONTRACT-2024-001"
    assert result.customer_id == sample_customer.id

    # Cleanup
    await test_session.execute(delete(Contract))
    await test_session.commit()


@pytest.mark.asyncio
async def test_get_by_id_not_found(contract_service, test_session):
    """
    Test get_by_id() returns None when contract doesn't exist
    """
    # Ensure database is empty
    await test_session.execute(delete(Contract))
    await test_session.commit()

    # Try to get non-existent contract
    non_existent_id = uuid4()
    result = await contract_service.get_by_id(non_existent_id)

    # Verify result is None
    assert result is None

    # Cleanup
    await test_session.execute(delete(Contract))
    await test_session.commit()


@pytest.mark.asyncio
async def test_get_by_id_with_none_id(contract_service):
    """
    Test get_by_id() returns None when contract_id is None
    """
    result = await contract_service.get_by_id(None)  # type: ignore[arg-type]
    assert result is None


@pytest.mark.asyncio
async def test_get_all_empty(contract_service, test_session):
    """
    Test get_all() returns empty list when database is empty
    """
    # Ensure database is empty
    await test_session.execute(delete(Contract))
    await test_session.commit()

    result = await contract_service.get_all()

    assert result == []
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_get_all_with_contracts(contract_service, test_session, sample_customer):
    """
    Test get_all() returns all contracts
    """
    # Ensure database is empty
    await test_session.execute(delete(Contract))
    await test_session.commit()

    from app.api.schemas.contract import ContractWrite

    start_date = datetime.now()
    end_date = start_date + timedelta(days=365)

    # Create multiple contracts
    contract1_data = ContractWrite(
        customer_id=sample_customer.id,
        product_name="商品1",
        start_date=start_date,
        end_date=end_date,
        monthly_rent=10000,
        billing_interval=BillingInterval.THREE_MONTHS,
        status=ContractStatus.ACTIVE,
    )

    contract2_data = ContractWrite(
        customer_id=sample_customer.id,
        product_name="商品2",
        start_date=start_date,
        end_date=end_date,
        monthly_rent=15000,
        billing_interval=BillingInterval.SIX_MONTHS,
        status=ContractStatus.PENDING,
    )

    contract3_data = ContractWrite(
        customer_id=sample_customer.id,
        product_name="商品3",
        start_date=start_date,
        end_date=end_date,
        monthly_rent=20000,
        billing_interval=BillingInterval.TWELVE_MONTHS,
        status=ContractStatus.ACTIVE,
    )

    await contract_service.create(contract1_data)
    await contract_service.create(contract2_data)
    await contract_service.create(contract3_data)

    result = await contract_service.get_all()

    # Verify returned count
    assert len(result) == 3

    # Verify each contract's data
    assert all(contract.id is not None for contract in result)
    assert all(contract.product_name is not None for contract in result)

    # Verify product names
    product_names = [contract.product_name for contract in result]
    assert "商品1" in product_names
    assert "商品2" in product_names
    assert "商品3" in product_names

    # Verify monthly rents
    monthly_rents = [contract.monthly_rent for contract in result]
    assert 10000 in monthly_rents
    assert 15000 in monthly_rents
    assert 20000 in monthly_rents

    # Verify billing intervals
    billing_intervals = [contract.billing_interval for contract in result]
    assert BillingInterval.THREE_MONTHS in billing_intervals
    assert BillingInterval.SIX_MONTHS in billing_intervals
    assert BillingInterval.TWELVE_MONTHS in billing_intervals

    # Verify statuses
    statuses = [contract.status for contract in result]
    assert ContractStatus.ACTIVE in statuses
    assert ContractStatus.PENDING in statuses

    # Cleanup
    await test_session.execute(delete(Contract))
    await test_session.commit()


@pytest.mark.asyncio
async def test_get_all_filtered_by_customer_id(contract_service, test_session):
    """
    Test get_all() with customer_id filter returns only that customer's contracts
    """
    # Ensure database is empty
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()

    # Create customers
    customer1 = Customer(
        customer_name="客戶1",
        invoice_title="發票抬頭1",
        invoice_number="INV001",
        contact_phone="0912345678",
        messaging_app_line="line_id_1",
        address="台北市信義區",
        primary_contact="張三",
        customer_type=CustomerType.COMPANY,
    )
    customer2 = Customer(
        customer_name="客戶2",
        invoice_title="發票抬頭2",
        invoice_number="INV002",
        contact_phone="0923456789",
        messaging_app_line="line_id_2",
        address="新北市板橋區",
        primary_contact="李四",
        customer_type=CustomerType.REAL_ESTATE,
    )
    test_session.add(customer1)
    test_session.add(customer2)
    await test_session.commit()
    await test_session.refresh(customer1)
    await test_session.refresh(customer2)

    from app.api.schemas.contract import ContractWrite

    start_date = datetime.now()
    end_date = start_date + timedelta(days=365)

    # Create contracts for customer 1
    contract1_data = ContractWrite(
        customer_id=customer1.id,
        product_name="客戶1商品1",
        start_date=start_date,
        end_date=end_date,
        monthly_rent=10000,
        billing_interval=BillingInterval.THREE_MONTHS,
        status=ContractStatus.ACTIVE,
    )

    contract2_data = ContractWrite(
        customer_id=customer1.id,
        product_name="客戶1商品2",
        start_date=start_date,
        end_date=end_date,
        monthly_rent=15000,
        billing_interval=BillingInterval.SIX_MONTHS,
        status=ContractStatus.ACTIVE,
    )

    # Create contract for customer 2
    contract3_data = ContractWrite(
        customer_id=customer2.id,
        product_name="客戶2商品1",
        start_date=start_date,
        end_date=end_date,
        monthly_rent=20000,
        billing_interval=BillingInterval.TWELVE_MONTHS,
        status=ContractStatus.ACTIVE,
    )

    await contract_service.create(contract1_data)
    await contract_service.create(contract2_data)
    await contract_service.create(contract3_data)

    # Get contracts for customer 1
    result = await contract_service.get_all(customer_id=customer1.id)

    # Verify only customer 1's contracts are returned
    assert len(result) == 2

    # Verify all contracts belong to customer 1
    assert all(contract.customer_id == customer1.id for contract in result)

    # Verify product names
    product_names = [contract.product_name for contract in result]
    assert "客戶1商品1" in product_names
    assert "客戶1商品2" in product_names
    assert "客戶2商品1" not in product_names

    # Get contracts for customer 2
    result2 = await contract_service.get_all(customer_id=customer2.id)

    # Verify only customer 2's contracts are returned
    assert len(result2) == 1
    assert result2[0].customer_id == customer2.id
    assert result2[0].product_name == "客戶2商品1"

    # Cleanup
    await test_session.execute(delete(Contract))
    await test_session.execute(delete(Customer))
    await test_session.commit()


@pytest.mark.asyncio
async def test_get_all_filtered_by_nonexistent_customer_id(
    contract_service, test_session, sample_customer
):
    """
    Test get_all() with non-existent customer_id returns empty list
    """
    # Ensure database is empty
    await test_session.execute(delete(Contract))
    await test_session.commit()

    # Create a contract for sample_customer
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
        status=ContractStatus.ACTIVE,
    )

    await contract_service.create(contract_data)

    # Try to get contracts for non-existent customer
    non_existent_customer_id = uuid4()
    result = await contract_service.get_all(customer_id=non_existent_customer_id)

    # Verify empty list is returned
    assert result == []
    assert isinstance(result, list)

    # Cleanup
    await test_session.execute(delete(Contract))
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
async def test_delete_contract_success(contract_service, test_session, sample_customer):
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
