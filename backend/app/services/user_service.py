from sqlalchemy.ext.asyncio import AsyncSession


class UserService:
    """Customer service for managing customer data in database"""

    def __init__(self, session: AsyncSession):
        """Initialize the service with database session"""
        self._session = session
