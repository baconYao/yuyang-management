from uuid import UUID

from fastapi import APIRouter

from app.api.dependencies import UserServiceDep
from app.api.schemas.user import UserRead, UserWrite

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=list[UserRead])
async def get_users(service: UserServiceDep):
    """
    Get all users
    """
    pass


@router.get("/{user_id}", response_model=UserRead)
async def get_user_by_id(user_id: UUID, service: UserServiceDep):
    """
    Get a user by ID
    """
    pass


# This endpoint is only for admin to create user, normal user cannot create
# user. There's no way to create user via normal user.
@router.post("/", response_model=UserRead)
async def create_user(user: UserWrite, service: UserServiceDep):
    """
    Create a user
    """
    # TODO: Implement create user, only admin can create user
    pass


@router.put("/{user_id}", response_model=UserRead)
async def update_user(user_id: UUID, user: UserWrite, service: UserServiceDep):
    """
    Update a user
    """
    # TODO: Implement update user, only admin can update user
    # TODO: Able to freeze user, only admin can freeze user
    pass
