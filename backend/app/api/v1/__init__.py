from fastapi import APIRouter

from app.api.v1 import customers, users

router = APIRouter()

router.include_router(customers.router)
router.include_router(users.router)
