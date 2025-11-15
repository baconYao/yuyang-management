from fastapi import APIRouter

from app.api.v1 import customers

router = APIRouter()

router.include_router(customers.router)
