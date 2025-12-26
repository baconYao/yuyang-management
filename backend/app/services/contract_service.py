from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.contract import (
    ContractRead,
    ContractUpdate,
    ContractWrite,
)


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
        # TODO: Implement contract retrieval logic
        raise NotImplementedError

    async def get_all(self, customer_id: UUID | None = None) -> list[ContractRead]:  # noqa: E501
        """
        Get all contracts, optionally filtered by customer_id

        Args:
            customer_id: Optional customer ID to filter contracts

        Returns:
            List of contracts
        """
        # TODO: Implement contract retrieval logic
        raise NotImplementedError

    async def create(self, contract: ContractWrite) -> ContractRead | None:
        """
        Create a new contract

        Args:
            contract: Contract data to create

        Returns:
            Created contract with assigned ID
        """
        # TODO: Implement contract creation logic
        raise NotImplementedError

    async def delete(self, contract_id: UUID) -> bool:
        """
        Delete a contract by ID

        Args:
            contract_id: The ID of the contract to delete

        Returns:
            True if contract was deleted, False if contract not found
        """
        # TODO: Implement contract deletion logic
        raise NotImplementedError

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
