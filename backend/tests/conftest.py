import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.main import app


@pytest_asyncio.fixture(scope="session")
async def client():
    """
    Create FastAPI test client
    """
    # return TestClient(app)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as test_client:
        yield test_client


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

        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Cleanup: drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def test_session(test_engine):
    """
    Create test database session
    (session scope, shared across entire test session)
    """
    async_session = sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
