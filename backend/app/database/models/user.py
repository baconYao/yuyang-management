from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String
from sqlalchemy.dialects import postgresql
from sqlmodel import Column, Field, SQLModel

from app.api.schemas.user import UserType


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: UUID = Field(
        sa_column=Column(
            postgresql.UUID,
            default=uuid4,
            primary_key=True,
        )
    )
    created_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
        )
    )
    updated_at: datetime = Field(
        sa_column=Column(
            postgresql.TIMESTAMP,
            default=datetime.now,
            onupdate=datetime.now,
        )
    )

    name: str = Field(
        sa_column=Column(String(4), nullable=False),
        description="User name (max 4 traditional Chinese characters)",
    )
    email: str = Field(
        sa_column=Column(String, nullable=False, unique=True),
    )
    user_type: UserType
    contact_phone: str = Field(
        sa_column=Column(String, nullable=False, unique=True),
    )
    messaging_app_line: str
    address: str
    password_hash: str = Field(
        sa_column=Column(String, nullable=False),
        description="Hashed password",
    )
