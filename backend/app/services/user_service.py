from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.api.schemas.user import UserCreate, UserRead
from app.core.security import hash_password
from app.database.models.user import User


class UserService:
    """Customer service for managing customer data in database"""

    def __init__(self, session: AsyncSession):
        """Initialize the service with database session"""
        self._session = session

    async def create(self, user: UserCreate) -> UserRead | None:
        """
        Create a user
        """

        if user is None:
            return None

        # Check if user with this email already exists
        statement = select(User).where(User.email == user.email)
        result = await self._session.execute(statement)
        existing_user = result.scalar_one_or_none()
        if existing_user is not None:
            raise ValueError("User with this email already exists")

        # Create database model instance
        db_user = User(
            **user.model_dump(exclude=["password"]),
            password_hash=hash_password(user.password),
        )

        self._session.add(db_user)
        await self._session.commit()
        await self._session.refresh(db_user)

        return UserRead.model_validate(db_user)
