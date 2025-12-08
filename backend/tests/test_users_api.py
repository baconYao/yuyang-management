from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import delete, select

from app.api.schemas.user import UserType
from app.database.models.user import User


@pytest.mark.asyncio
async def test_get_users_empty(client: AsyncClient, test_session):
    """
    Test GET /api/v1/users/ returns empty list when database is empty
    This verifies that the API endpoint uses the test database.
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    response = await client.get("/api/v1/users/")
    assert response.status_code == 200
    data = response.json()
    assert data == []


@pytest.mark.asyncio
async def test_create_user_via_api(client: AsyncClient, test_session):
    """
    Test POST /api/v1/users/ creates a user in the test database
    This verifies that the API endpoint uses the test database, not production.
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    # Create user via API
    user_data = {
        "name": "測試",
        "email": "test@example.com",
        "user_type": "NORMAL",
        "contact_phone": "0911111111",
        "messaging_app_line": "test_line",
        "address": "Test Address",
    }

    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    created_user = response.json()

    # Verify response
    assert created_user["name"] == "測試"
    assert created_user["email"] == "test@example.com"
    assert created_user["user_type"] == "NORMAL"
    assert created_user["id"] is not None

    # Verify user exists in test database
    # Convert string ID to UUID object
    user_id = UUID(created_user["id"])
    result = await test_session.execute(
        select(User).where(
            User.id == user_id  # type: ignore[arg-type]
        )
    )
    db_user = result.scalar_one_or_none()
    assert db_user is not None
    assert db_user.name == "測試"
    assert db_user.email == "test@example.com"
    assert db_user.user_type == UserType.NORMAL

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()


@pytest.mark.asyncio
async def test_get_users_with_data(client: AsyncClient, test_session):
    """
    Test GET /api/v1/users/ returns users from test database
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    # Create test user directly in test database
    test_user = User(
        name="直接",
        email="direct@example.com",
        user_type=UserType.ADMIN,
        contact_phone="0922222222",
        messaging_app_line="direct_line",
        address="Direct Test Address",
    )
    test_session.add(test_user)
    await test_session.commit()
    await test_session.refresh(test_user)

    # Get users via API
    response = await client.get("/api/v1/users/")
    assert response.status_code == 200
    users = response.json()

    # Verify API returns the user we created directly in test DB
    assert len(users) == 1
    assert users[0]["name"] == "直接"
    assert users[0]["email"] == "direct@example.com"
    assert users[0]["user_type"] == "ADMIN"
    assert users[0]["id"] == str(test_user.id)

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()


@pytest.mark.asyncio
async def test_get_user_by_id_success(client: AsyncClient, test_session):
    """
    Test GET /api/v1/users/{user_id} returns user when found
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    # Create test user directly in test database
    test_user = User(
        name="查詢",
        email="query@example.com",
        user_type=UserType.NORMAL,
        contact_phone="0933333333",
        messaging_app_line="query_line",
        address="Query Test Address",
    )
    test_session.add(test_user)
    await test_session.commit()
    await test_session.refresh(test_user)

    # Get user by ID via API
    user_id = str(test_user.id)
    response = await client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    user = response.json()

    # Verify response data
    assert user["id"] == user_id
    assert user["name"] == "查詢"
    assert user["email"] == "query@example.com"
    assert user["user_type"] == "NORMAL"
    assert user["contact_phone"] == "0933333333"
    assert user["messaging_app_line"] == "query_line"
    assert user["address"] == "Query Test Address"

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(client: AsyncClient, test_session):
    """
    Test GET /api/v1/users/{user_id} returns 404
    when user not found
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    # Try to get non-existent user
    non_existent_id = str(uuid4())
    response = await client.get(f"/api/v1/users/{non_existent_id}")
    assert response.status_code == 404
    error_detail = response.json()
    assert "detail" in error_detail
    assert non_existent_id in error_detail["detail"]
    assert "not found" in error_detail["detail"].lower()


@pytest.mark.asyncio
async def test_get_user_by_id_invalid_uuid(client: AsyncClient):
    """
    Test GET /api/v1/users/{user_id} returns 422
    for invalid UUID format
    """
    # Try to get user with invalid UUID format
    invalid_id = "not-a-valid-uuid"
    response = await client.get(f"/api/v1/users/{invalid_id}")
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
    }

    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 422
    error_detail = response.json()
    assert "detail" in error_detail

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
