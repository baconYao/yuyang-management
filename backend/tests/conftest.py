import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.database.session import get_session
from app.main import app


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """
    Create SQLite test database engine
    (session scope, shared across entire test session)
    """
    # Use SQLite in-memory database for testing
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        # Need to import all models so SQLModel knows which tables to create
        from app.database.models.customer import Customer  # noqa: F401
        from app.database.models.user import User  # noqa: F401

        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Cleanup: drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def test_session_factory(test_engine):
    """
    Create test database session factory
    (session scope, shared across entire test session)
    """
    async_session = sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return async_session


@pytest_asyncio.fixture(scope="session")
async def test_session(test_session_factory):
    """
    Create test database session
    (session scope, shared across entire test session)
    """
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def client(test_engine, test_session_factory):
    """
    Create FastAPI test client with test database override

    This fixture overrides the database session dependency to use the test
    database instead of the production database, ensuring test isolation.
    """

    # Override get_session dependency to use test database
    async def get_test_session():
        async with test_session_factory() as session:
            yield session

    # Override the dependency
    app.dependency_overrides[get_session] = get_test_session

    # Temporarily replace the production engine with test engine
    # This ensures lifespan handler uses test database
    import app.database.session as session_module

    original_engine = session_module.engine
    session_module.engine = test_engine

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as test_client:
        yield test_client

    # Cleanup: restore original dependencies and engine
    app.dependency_overrides.clear()
    session_module.engine = original_engine
