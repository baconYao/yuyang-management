from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import ContractServiceDep
from app.api.schemas.contract import (
    ContractRead,
    ContractUpdate,
    ContractWrite,
)

router = APIRouter(prefix="/contracts", tags=["Contracts"])


@router.post(
    "/",
    response_model=ContractRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_contract(contract: ContractWrite, service: ContractServiceDep):  # noqa: E501
    """
    Create a new contract

    Args:
        contract: Contract data to create

    Returns:
        Created contract with assigned ID
    """
    created_contract = await service.create(contract)
    if created_contract is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create contract",
        )
    return created_contract


@router.get("/{contract_id}", response_model=ContractRead)
async def get_contract_by_id(contract_id: UUID, service: ContractServiceDep):
    """
    Get a contract by ID

    Args:
        contract_id: The ID of the contract to retrieve

    Returns:
        Contract information

    Raises:
        HTTPException: If contract not found
    """
    contract = await service.get_by_id(contract_id)
    if contract is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with ID {contract_id} not found",
        )
    return contract


@router.get("/", response_model=list[ContractRead])
async def get_contracts(
    service: ContractServiceDep,
    customer_id: UUID | None = Query(
        None, description="Optional customer ID to filter contracts"
    ),
):
    """
    Get all contracts, optionally filtered by customer_id

    Args:
        customer_id: Optional customer ID to filter contracts.
                     If provided, returns contracts for that customer.
                     If not provided, returns all contracts.
        service: Contract service dependency

    Returns:
        List of contracts
    """
    contracts = await service.get_all(customer_id=customer_id)
    return contracts


@router.patch("/{contract_id}", response_model=ContractRead)
async def update_contract_by_id(
    contract_id: UUID,
    contract: ContractUpdate,
    service: ContractServiceDep,
):
    """
    Update a contract by ID

    Args:
        contract_id: The ID of the contract to update
        contract: Contract data to update (partial update supported)

    Returns:
        Updated contract information

    Raises:
        HTTPException: If contract not found
    """
    if contract_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract ID is required",
        )

    updated_contract = await service.update(contract_id, contract)
    return updated_contract


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(contract_id: UUID, service: ContractServiceDep):
    """
    Delete a contract by ID

    Args:
        contract_id: The ID of the contract to delete

    Raises:
        HTTPException: If contract not found
    """
    if contract_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contract ID is required",
        )

    deleted = await service.delete(contract_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fialed to delete contract with ID {contract_id}",
        )
