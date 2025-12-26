from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import validate_password


class UserType(str, Enum):
    """User type enumeration"""

    ADMIN = "ADMIN"
    NORMAL = "NORMAL"


class BaseUser(BaseModel):
    """Base user information schema"""

    name: str = Field(
        ...,
        max_length=4,
        description="User name (max 4 traditional Chinese characters)",
    )
    email: EmailStr = Field(..., description="User email address")
    user_type: UserType = Field(..., description="User type")
    contact_phone: str = Field(..., description="Contact phone number")
    messaging_app_line: str = Field(..., description="Messaging app")
    address: str = Field(..., description="Address")


class UserRead(BaseUser):
    """User information read schema"""

    id: UUID | None = Field(None, description="User ID")

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseUser):
    """User information write schema"""

    password: str = Field(..., description="User password")

    @field_validator("password")
    @classmethod
    def validate_password_field(cls, v: str) -> str:
        """Validate password using security module"""
        validate_password(v)
        return v


class UserUpdate(BaseModel):
    """User information update schema"""

    name: str | None = Field(
        None,
        max_length=4,
        description="User name (max 4 traditional Chinese characters)",
    )
    email: EmailStr | None = Field(None, description="User email address")
    user_type: UserType | None = Field(None, description="User type")
    contact_phone: str | None = Field(None, description="Contact phone number")
    messaging_app_line: str | None = Field(None, description="Messaging app")
    address: str | None = Field(None, description="Address")
