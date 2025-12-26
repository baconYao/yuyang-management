from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.config import db_settings

# Create a database engine to connect with database
engine = create_async_engine(
    # database type/dialect and file name
    url=db_settings.POSTGRES_URL,
    # Log sql queries
    echo=True,
)


async def create_db_tables():
    async with engine.begin() as connection:
        # # SQLModel 只有在 Model 被 import 時才會把它加入 metadata。
        # 不 import 的話 create_all() 與 ORM 都不會知道這個 Model 的存在。
        # （與 Alembic 是否已經建表無關）
        from app.database.models.customer import Customer  # noqa: F401
        from app.database.models.user import User  # noqa: F401

        await connection.run_sync(SQLModel.metadata.create_all)


async def get_session():
    async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
