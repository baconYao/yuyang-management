from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import BillServiceDep
from app.api.schemas.bill import BillRead, BillStatus, BillUpdate, BillWrite
from app.services.bill_service import InvalidStatusTransitionError

router = APIRouter(prefix="/bills", tags=["Bills"])


@router.post(
    "/",
    response_model=BillRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_bill(bill: BillWrite, service: BillServiceDep):
    """
    Create a new bill.

    Args:
        bill: Bill data to create

    Returns:
        Created bill with assigned bill_number

    Raises:
        HTTPException: If customer/contract not found or create failed
    """
    created = await service.create(bill)
    if created is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create bill (customer_id or contract_id may not exist)",  # noqa: E501
        )
    return created


# List route must be before /{bill_number} so GET /bills/?status=...
# is not matched as bill_number=""
@router.get("/", response_model=list[BillRead])
async def get_bills(
    service: BillServiceDep,
    customer_id: UUID | None = Query(
        None, description="Optional customer ID to filter bills"
    ),
    contract_id: UUID | None = Query(
        None, description="Optional contract ID to filter bills"
    ),
    status: list[BillStatus] | None = Query(
        None,
        description="Optional list of statuses to filter bills (e.g. DRAFT, PAID)",  # noqa: E501
    ),
):
    """
    Get all bills, optionally filtered by customer_id, contract_id, or status.

    Returns:
        List of bills (ordered by created_at descending).
    """
    return await service.get_all(
        customer_id=customer_id,
        contract_id=contract_id,
        statuses=status,
    )


@router.get("/{bill_number}", response_model=BillRead)
async def get_bill_by_bill_number(bill_number: str, service: BillServiceDep):
    """
    Get a bill by bill_number (primary key).

    Args:
        bill_number: The bill number (primary key) of the bill to retrieve

    Returns:
        Bill information

    Raises:
        HTTPException: If bill not found
    """
    bill = await service.get_by_bill_number(bill_number)
    if bill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill with bill_number {bill_number!r} not found",
        )
    return bill


@router.patch("/{bill_number}", response_model=BillRead)
async def update_bill_by_bill_number(
    bill_number: str,
    bill: BillUpdate,
    service: BillServiceDep,
):
    """
    Update a bill by bill_number (primary key, partial update supported).

    Args:
        bill_number: The bill number (primary key) of the bill to update
        bill: Bill data to update

    Returns:
        Updated bill

    Raises:
        HTTPException: If bill not found
    """
    try:
        return await service.update(bill_number, bill)
    except InvalidStatusTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
