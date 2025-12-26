# flake8: noqa: E501
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select

from app.api.schemas.user import UserType
from app.database.models.user import User


@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient, test_session):
    """
    Test POST /api/v1/users/ successfully creates a user
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    # Create user via API
    user_data = {
        "name": "張培堯",
        "email": "test@example.com",
        "user_type": "ADMIN",
        "contact_phone": "0912345678",
        "messaging_app_line": "test_line",
        "address": "Test Address",
        "password": "Test1234!",
    }

    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    created_user = response.json()

    # Verify response
    assert created_user["name"] == "張培堯"
    assert created_user["email"] == "test@example.com"
    assert created_user["user_type"] == "ADMIN"
    assert created_user["contact_phone"] == "0912345678"
    assert created_user["messaging_app_line"] == "test_line"
    assert created_user["address"] == "Test Address"
    assert created_user["id"] is not None
    # Password should not be in response
    assert "password" not in created_user
    assert "password_hash" not in created_user

    # Verify user exists in test database
    user_id = UUID(created_user["id"])
    result = await test_session.execute(
        select(User).where(User.id == user_id)  # type: ignore[arg-type]
    )
    db_user = result.scalar_one_or_none()
    assert db_user is not None
    assert db_user.name == "張培堯"
    assert db_user.email == "test@example.com"
    assert db_user.user_type == UserType.ADMIN
    assert db_user.password_hash is not None
    assert db_user.password_hash != "Test1234!"  # Should be hashed

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_user_missing_required_fields(client: AsyncClient):
    """
    Test POST /api/v1/users/ returns 422
    for missing required fields
    """
    # Try to create user with missing required fields
    user_data = {
        "name": "測試",
        # Missing email and other required fields
    }

    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail


@pytest.mark.asyncio
async def test_create_user_invalid_email(client: AsyncClient, test_session):
    """
    Test POST /api/v1/users/ returns 422
    for invalid email format
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    # Try to create user with invalid email
    user_data = {
        "name": "測試",
        "email": "invalid-email",
        "user_type": "NORMAL",
        "contact_phone": "0911111111",
        "messaging_app_line": "test_line",
        "address": "Test Address",
        "password": "Test1234!",
    }

    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_user_name_too_long(client: AsyncClient, test_session):
    """
    Test POST /api/v1/users/ returns 422
    for name exceeding max length (4 characters)
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    # Try to create user with name too long
    user_data = {
        "name": "測試名稱太長",
        "email": "test@example.com",
        "user_type": "NORMAL",
        "contact_phone": "0911111111",
        "messaging_app_line": "test_line",
        "address": "Test Address",
        "password": "Test1234!",
    }

    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_user_password_too_short(client: AsyncClient, test_session):
    """
    Test POST /api/v1/users/ returns 422
    for password too short (less than 8 characters)
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    # Try to create user with password too short
    user_data = {
        "name": "測試",
        "email": "test@example.com",
        "user_type": "NORMAL",
        "contact_phone": "0911111111",
        "messaging_app_line": "test_line",
        "address": "Test Address",
        "password": "Test1!",
    }

    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail
    # Pydantic validation errors are in a list format
    error_str = str(error_detail["detail"])
    assert "8-16 characters" in error_str

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_user_password_too_long(client: AsyncClient, test_session):
    """
    Test POST /api/v1/users/ returns 422
    for password too long (more than 16 characters)
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    # Try to create user with password too long (17 characters)
    user_data = {
        "name": "測試",
        "email": "test@example.com",
        "user_type": "NORMAL",
        "contact_phone": "0911111111",
        "messaging_app_line": "test_line",
        "address": "Test Address",
        "password": "Test123456789012!",
    }

    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail
    # Pydantic validation errors are in a list format
    error_str = str(error_detail["detail"])
    assert "8-16 characters" in error_str

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_user_password_no_uppercase(client: AsyncClient, test_session):
    """
    Test POST /api/v1/users/ returns 422
    for password without uppercase letter
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    # Try to create user with password without uppercase
    user_data = {
        "name": "測試",
        "email": "test@example.com",
        "user_type": "NORMAL",
        "contact_phone": "0911111111",
        "messaging_app_line": "test_line",
        "address": "Test Address",
        "password": "test1234!",
    }

    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail
    # Pydantic validation errors are in a list format
    error_str = str(error_detail["detail"]).lower()
    assert "uppercase" in error_str

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_user_password_no_lowercase(client: AsyncClient, test_session):
    """
    Test POST /api/v1/users/ returns 422
    for password without lowercase letter
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    # Try to create user with password without lowercase
    user_data = {
        "name": "測試",
        "email": "test@example.com",
        "user_type": "NORMAL",
        "contact_phone": "0911111111",
        "messaging_app_line": "test_line",
        "address": "Test Address",
        "password": "TEST1234!",
    }

    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail
    # Pydantic validation errors are in a list format
    error_str = str(error_detail["detail"]).lower()
    assert "lowercase" in error_str

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_user_password_no_special(client: AsyncClient, test_session):
    """
    Test POST /api/v1/users/ returns 422
    for password without special character
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    # Try to create user with password without special character
    user_data = {
        "name": "測試",
        "email": "test@example.com",
        "user_type": "NORMAL",
        "contact_phone": "0911111111",
        "messaging_app_line": "test_line",
        "address": "Test Address",
        "password": "Test1234",
    }

    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail
    # Pydantic validation errors are in a list format
    error_str = str(error_detail["detail"]).lower()
    assert "special character" in error_str

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_user_password_invalid_characters(
    client: AsyncClient, test_session
):
    """
    Test POST /api/v1/users/ returns 422
    for password with invalid characters
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    # Try to create user with password containing invalid characters
    user_data = {
        "name": "測試",
        "email": "test@example.com",
        "user_type": "NORMAL",
        "contact_phone": "0911111111",
        "messaging_app_line": "test_line",
        "address": "Test Address",
        "password": "Test124!<///>",
    }

    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail
    # Pydantic validation errors are in a list format
    error_str = str(error_detail["detail"]).lower()
    assert "invalid" in error_str

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient, test_session):
    """
    Test POST /api/v1/users/ returns 409
    when trying to create user with duplicate email
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    # Create first user via API
    user_data = {
        "name": "測試",
        "email": "duplicate@example.com",
        "user_type": "NORMAL",
        "contact_phone": "0911111111",
        "messaging_app_line": "test_line",
        "address": "Test Address",
        "password": "Test1234!",
    }

    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201

    # Try to create another user with same email
    duplicate_user_data = {
        "name": "測試二",
        "email": "duplicate@example.com",
        "user_type": "ADMIN",
        "contact_phone": "0922222222",
        "messaging_app_line": "test_line2",
        "address": "Test Address 2",
        "password": "Test5678!",
    }

    response = await client.post("/api/v1/users/", json=duplicate_user_data)
    assert response.status_code == 409
    error_detail = response.json()
    assert "detail" in error_detail
    assert "already exists" in error_detail["detail"].lower()

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()
