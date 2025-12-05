from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.services.customer_service import CustomerService

# Asynchronous database session dep annotation
SessionDep = Annotated[AsyncSession, Depends(get_session)]


# Customer service dep with session
def get_customer_service(session: SessionDep) -> CustomerService:
    """
    Get CustomerService instance with database session

    Args:
        session: Database session

    Returns:
        CustomerService instance
    """
    return CustomerService(session)


# Customer service dep annotation
CustomerServiceDep = Annotated[
    CustomerService,
    Depends(get_customer_service),
]
