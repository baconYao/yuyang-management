import pytest
import pytest_asyncio
from sqlalchemy import delete, select

from app.api.schemas.user import UserCreate, UserType
from app.core.security import pwd_context
from app.database.models.user import User
from app.services.user_service import UserService


@pytest_asyncio.fixture(scope="function")
async def user_service(test_session):
    """
    Create UserService instance
    """
    return UserService(test_session)


@pytest.mark.asyncio
async def test_create_user_success(user_service, test_session):
    """
    Test create() successfully creates a user
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    # Create user data
    user_data = UserCreate(
        name="張培堯",
        email="test@example.com",
        user_type=UserType.ADMIN,
        contact_phone="0912345678",
        messaging_app_line="test_line",
        address="Test Address",
        password="Test1234!",
    )

    # Create user via service
    result = await user_service.create(user_data)

    # Verify result is not None
    assert result is not None
    assert result.id is not None
    assert result.name == "張培堯"
    assert result.email == "test@example.com"
    assert result.user_type == UserType.ADMIN
    assert result.contact_phone == "0912345678"
    assert result.messaging_app_line == "test_line"
    assert result.address == "Test Address"
    # Password should not be in result
    assert not hasattr(result, "password")
    assert not hasattr(result, "password_hash")

    # Verify user exists in database
    statement = select(User).where(User.id == result.id)
    db_result = await test_session.execute(statement)
    db_user = db_result.scalar_one_or_none()

    assert db_user is not None
    assert db_user.name == "張培堯"
    assert db_user.email == "test@example.com"
    assert db_user.user_type == UserType.ADMIN
    assert db_user.contact_phone == "0912345678"
    assert db_user.messaging_app_line == "test_line"
    assert db_user.address == "Test Address"
    assert db_user.password_hash is not None
    # Verify password is hashed (not plain text)
    assert db_user.password_hash != "Test1234!"
    # Verify password hash can be verified
    assert pwd_context.verify("Test1234!", db_user.password_hash)

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_user_with_none_input(user_service):
    """
    Test create() returns None when user is None
    """
    result = await user_service.create(None)
    assert result is None


@pytest.mark.asyncio
async def test_create_user_duplicate_email(user_service, test_session):
    """
    Test create() raises ValueError when email already exists
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    # Create first user
    user_data1 = UserCreate(
        name="測試",
        email="duplicate@example.com",
        user_type=UserType.NORMAL,
        contact_phone="0911111111",
        messaging_app_line="test_line",
        address="Test Address",
        password="Test1234!",
    )

    result1 = await user_service.create(user_data1)
    assert result1 is not None

    # Try to create another user with same email
    user_data2 = UserCreate(
        name="測試二",
        email="duplicate@example.com",
        user_type=UserType.ADMIN,
        contact_phone="0922222222",
        messaging_app_line="test_line2",
        address="Test Address 2",
        password="Test5678!",
    )

    # Should raise ValueError
    with pytest.raises(ValueError) as exc_info:
        await user_service.create(user_data2)

    assert "email already exists" in str(exc_info.value).lower()

    # Verify only one user exists in database
    statement = select(User)
    db_result = await test_session.execute(statement)
    users = db_result.scalars().all()
    assert len(users) == 1
    assert users[0].email == "duplicate@example.com"

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_user_password_is_hashed(user_service, test_session):
    """
    Test create() properly hashes the password
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    password = "SecurePass123!"
    user_data = UserCreate(
        name="測試",
        email="hash_test@example.com",
        user_type=UserType.NORMAL,
        contact_phone="0933333333",
        messaging_app_line="test_line",
        address="Test Address",
        password=password,
    )

    result = await user_service.create(user_data)
    assert result is not None

    # Verify password is hashed in database
    statement = select(User).where(User.id == result.id)
    db_result = await test_session.execute(statement)
    db_user = db_result.scalar_one_or_none()

    assert db_user is not None
    assert db_user.password_hash != password
    assert len(db_user.password_hash) > 20  # bcrypt hashes are long
    # Verify hash can be verified
    assert pwd_context.verify(password, db_user.password_hash)
    # Verify wrong password doesn't work
    wrong_password = "WrongPassword123!"
    assert not pwd_context.verify(wrong_password, db_user.password_hash)

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()


@pytest.mark.asyncio
async def test_create_user_timestamps_set(user_service, test_session):
    """
    Test create() sets created_at and updated_at timestamps
    """
    # Ensure database is empty
    await test_session.execute(delete(User))
    await test_session.commit()

    user_data = UserCreate(
        name="測試",
        email="timestamp@example.com",
        user_type=UserType.NORMAL,
        contact_phone="0944444444",
        messaging_app_line="test_line",
        address="Test Address",
        password="Test1234!",
    )

    result = await user_service.create(user_data)
    assert result is not None

    # Verify timestamps are set in database
    statement = select(User).where(User.id == result.id)
    db_result = await test_session.execute(statement)
    db_user = db_result.scalar_one_or_none()

    assert db_user is not None
    assert db_user.created_at is not None
    assert db_user.updated_at is not None
    # Timestamps should be approximately equal
    # (created and updated at same time)
    time_diff = abs((db_user.created_at - db_user.updated_at).total_seconds())
    assert time_diff < 1  # Should be within 1 second

    # Cleanup
    await test_session.execute(delete(User))
    await test_session.commit()
