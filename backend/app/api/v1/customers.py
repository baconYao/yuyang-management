from fastapi import APIRouter

from app.api.schemas.customer import CustomerUpdate, CustomerWrite

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/")
async def get_customers():
    return {"customers": []}


@router.post("/")
async def create_customer(customer: CustomerWrite):
    return {"customer": customer}


@router.patch("/")
async def update_customer(customer: CustomerUpdate):
    return {"customer": customer}


@router.delete("/")
async def delete_customer(id: int) -> dict[str, str]:
    return {"status": "try"}
