from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.services.contract_service import ContractService
from app.services.customer_service import CustomerService
from app.services.user_service import UserService

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


def get_user_service(session: SessionDep) -> UserService:
    """
    Get UserService instance with database session

    Args:
        session: Database session

    Returns:
        UserService instance
    """
    return UserService(session)


def get_contract_service(session: SessionDep) -> ContractService:
    """
    Get ContractService instance with database session

    Args:
        session: Database session

    Returns:
        ContractService instance
    """
    return ContractService(session)


# Customer service dep annotation
CustomerServiceDep = Annotated[
    CustomerService,
    Depends(get_customer_service),
]

UserServiceDep = Annotated[
    UserService,
    Depends(get_user_service),
]

ContractServiceDep = Annotated[
    ContractService,
    Depends(get_contract_service),
]
