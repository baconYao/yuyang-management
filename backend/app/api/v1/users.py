from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import UserServiceDep
from app.api.schemas.user import UserCreate, UserRead, UserUpdate

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


# TODO: This endpoint is only for admin to create user, normal user cannot
# create user. There's no way to create user via normal user.
@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(user: UserCreate, service: UserServiceDep):
    """
    Create a user

    Args:
        user: User data to create

    Returns:
        Created user with assigned ID
    """
    try:
        created_user = await service.create(user)
        return created_user
    except ValueError as e:
        error_msg = str(e)
        # Check if it's an email duplicate error
        if "email already exists" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=error_msg,
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )
    except IntegrityError as e:
        # Handle database constraint violations (e.g., unique constraint)
        error_msg = str(e.orig) if hasattr(e, "orig") else str(e)
        if "unique" in error_msg.lower() or "duplicate" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database constraint violation: {error_msg}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}",
        )


@router.put("/{user_id}", response_model=UserRead)
async def update_user(user_id: UUID, user: UserUpdate, service: UserServiceDep):  # noqa: E501
    """
    Update a user
    """
    # TODO: Implement update user, only admin can update user
    # TODO: Able to freeze user, only admin can freeze user
    pass
