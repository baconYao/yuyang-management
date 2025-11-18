from typing import Annotated

from fastapi import Depends

from app.services.customer_service import CustomerService


# Customer service dep
def get_customer_service() -> CustomerService:
    """
    Get CustomerService instance

    Returns:
        CustomerService instance (singleton)
    """
    return CustomerService()


# Customer service dep annotation
CustomerServiceDep = Annotated[
    CustomerService,
    Depends(get_customer_service),
]

# Note: If database session is needed in the future, uncomment and configure:
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.database.session import get_session
#
# # Asynchronous database session dep annotation
# SessionDep = Annotated[AsyncSession, Depends(get_session)]
#
# # Customer service dep with session
# def get_customer_service(session: SessionDep) -> CustomerService:
#     """
#     Get CustomerService instance with database session
#
#     Args:
#         session: Database session
#
#     Returns:
#         CustomerService instance
#     """
#     return CustomerService(session)
#
# # Customer service dep annotation
# CustomerServiceDep = Annotated[
#     CustomerService,
#     Depends(get_customer_service),
# ]
