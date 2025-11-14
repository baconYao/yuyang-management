from fastapi import APIRouter

from app.api.v1 import hello

router = APIRouter()

router.include_router(hello.router, prefix="")
