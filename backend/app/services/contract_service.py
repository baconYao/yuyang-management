import logging
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.schemas.contract import (
    ContractRead,
    ContractUpdate,
    ContractWrite,
)
from app.database.models.contract import Contract
from app.database.models.customer import Customer

logger = logging.getLogger(__name__)


class ContractService:
    """Contract service for managing contract data in database"""

    def __init__(self, session: AsyncSession):
        """Initialize the service with database session"""
        self._session = session

    async def get_by_id(self, contract_id: UUID) -> ContractRead | None:
        """
        Get a contract by ID

        Args:
            contract_id: The ID of the contract to retrieve

        Returns:
            ContractRead if found, None otherwise
        """
        # Validate contract_id before querying database
        if contract_id is None:
            return None

        statement = select(Contract).where(Contract.id == contract_id)
        result = await self._session.execute(statement)
        db_contract = result.scalar_one_or_none()
        if db_contract is None:
            return None
        return ContractRead.model_validate(db_contract)

    async def get_all(self, customer_id: UUID | None = None) -> list[ContractRead]:  # noqa: E501
        """
        Get all contracts, optionally filtered by customer_id

        Args:
            customer_id: Optional customer ID to filter contracts

        Returns:
            List of contracts
        """
        if customer_id is None:
            # Get all contracts
            statement = select(Contract)
        else:
            # Get contracts filtered by customer_id
            statement = select(Contract).where(Contract.customer_id == customer_id)  # noqa: E501

        result = await self._session.execute(statement)
        db_contracts = result.scalars().all()
        return [ContractRead.model_validate(contract) for contract in db_contracts]  # noqa: E501

    async def create(self, contract: ContractWrite) -> ContractRead | None:
        """
        Create a new contract

        Args:
            contract: Contract data to create

        Returns:
            Created contract with assigned ID,
            None if customer_id doesn't exist
        """
        if contract is None:
            return None

        # Verify customer_id exists before creating contract
        customer_statement = select(Customer).where(Customer.id == contract.customer_id)  # noqa: E501
        customer_result = await self._session.execute(customer_statement)
        db_customer = customer_result.scalar_one_or_none()
        if db_customer is None:
            logger.warning(
                f"Failed to create contract: customer_id "
                f"{contract.customer_id} does not exist"
            )
            return None

        # Create database model instance
        db_contract = Contract(
            customer_id=contract.customer_id,
            product_name=contract.product_name,
            start_date=contract.start_date,
            end_date=contract.end_date,
            monthly_rent=contract.monthly_rent,
            billing_interval=contract.billing_interval,
            notes=contract.notes,
            status=contract.status,
            contract_number=contract.contract_number,
            signed_date=contract.signed_date,
            payment_method=contract.payment_method,
            next_billing_date=contract.next_billing_date,
            terminated_at=contract.terminated_at,
            termination_reason=contract.termination_reason,
        )

        # Add to session and commit
        self._session.add(db_contract)
        await self._session.commit()
        await self._session.refresh(db_contract)

        # Convert to read schema
        return ContractRead.model_validate(db_contract)

    async def delete(self, contract_id: UUID) -> bool:
        """
        Delete a contract by ID

        Args:
            contract_id: The ID of the contract to delete

        Returns:
            True if contract was deleted, False if contract not found
        """
        # Validate contract_id before querying database
        if contract_id is None:
            return False

        # Get contract first to check if it exists
        statement = select(Contract).where(Contract.id == contract_id)
        result = await self._session.execute(statement)
        db_contract = result.scalar_one_or_none()
        if db_contract is None:
            logger.warning(
                f"Failed to delete contract: contract_id {contract_id} does not exist"  # noqa: E501
            )
            return False

        # Delete the contract using delete statement
        delete_statement = delete(Contract).where(
            Contract.id == contract_id  # type: ignore[arg-type]
        )
        await self._session.execute(delete_statement)
        await self._session.commit()
        return True

    async def update(
        self, contract_id: UUID, contract_update: ContractUpdate
    ) -> ContractRead:
        """
        Update a contract by ID

        Args:
            contract_id: The ID of the contract to update
            contract_update: Contract data to update (partial update supported)

        Returns:
            ContractRead if contract was updated
        """
        # TODO: Implement contract update logic
        raise NotImplementedError
