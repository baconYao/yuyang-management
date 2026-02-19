import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import Response

from app.api.dependencies import BillServiceDep
from app.api.schemas.bill import BillRead, BillStatus, BillUpdate, BillWrite
from app.api.schemas.contract import InvoiceType
from app.pdf import generate_pdf_bytes
from app.services.bill_service import InvalidStatusTransitionError

logger = logging.getLogger(__name__)

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


def _invoice_type_to_str(invoice_type: InvoiceType) -> str:
    if invoice_type == InvoiceType.TRIPLE_UNIFORM_INVOICE:
        return "三聯"
    if invoice_type == InvoiceType.DUPLICATE_UNIFORM_INVOICE:
        return "二聯"
    return "無發票"


@router.get("/{bill_number}/pdf")
async def get_bill_pdf(bill_number: str, service: BillServiceDep):
    """
    Download bill as PDF (請款單).

    Returns:
        application/pdf with Content-Disposition attachment.
    """
    pair = await service.get_bill_with_customer(bill_number)
    if pair is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bill or customer not found for bill_number {bill_number!r}",  # noqa: E501
        )
    bill, customer = pair
    due_or_created = bill.due_date or bill.created_at
    invoice_issue_date = ""
    if due_or_created:
        dt = due_or_created
        if hasattr(dt, "strftime"):
            invoice_issue_date = dt.strftime("%Y-%m-%d")
        else:
            invoice_issue_date = str(dt)[:10]

    invoice_data = {
        "customer_name": customer.customer_name or "",
        "invoice_title": customer.invoice_title or "",
        "contact_person": customer.primary_contact or "",
        "phone": customer.contact_phone or "",
        "tax_id": customer.invoice_number or "",
        "invoice_number": customer.invoice_number or "",
        "invoice_type": _invoice_type_to_str(bill.invoice_type),
        "notes": bill.notes or "",
        "invoice_issue_date": invoice_issue_date,
        "address": customer.address or "",
        "items": [
            {
                "name": item.product_name or "",
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "amount": item.amount,
            }
            for item in bill.items
        ],
    }
    try:
        pdf_bytes = await asyncio.to_thread(generate_pdf_bytes, invoice_data)
    except Exception as e:
        logger.exception("Bill PDF generation failed for %s", bill_number)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PDF generation failed",
        ) from e
    filename = f"{bill_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
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
