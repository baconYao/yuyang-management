from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CustomerServiceDep
from app.api.schemas.customer import (
    CustomerRead,
    CustomerUpdate,
    CustomerWrite,
)

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/", response_model=list[CustomerRead])
async def get_customers(service: CustomerServiceDep):
    """
    Get all customers

    Returns:
        List of all customers
    """
    customers = await service.get_all()
    return customers


@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer_by_id(customer_id: UUID, service: CustomerServiceDep):
    """
    Get a customer by ID

    Args:
        customer_id: The ID of the customer to retrieve

    Returns:
        Customer information

    Raises:
        HTTPException: If customer not found
    """
    customer = await service.get_by_id(customer_id)
    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found",
        )
    return customer


@router.post(
    "/",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_customer(customer: CustomerWrite, service: CustomerServiceDep):  # noqa: E501
    """
    Create a new customer

    Args:
        customer: Customer data to create

    Returns:
        Created customer with assigned ID
    """
    created_customer = await service.create(customer)
    return created_customer


@router.patch("/")
async def update_customer(customer: CustomerUpdate):
    return {"customer": customer}


@router.delete("/")
async def delete_customer(id: int) -> dict[str, str]:
    return {"status": "try"}
