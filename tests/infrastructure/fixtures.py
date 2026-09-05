import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.database.engine import create_database_engine


@pytest_asyncio.fixture
async def test_session() -> AsyncSession:
    settings = get_settings()

    engine = create_database_engine(settings)

    async with engine.connect() as connection:
        transaction = await connection.begin()

        session_factory = async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
        )

        async with session_factory() as session:
            yield session

        if transaction.is_active:
            await transaction.rollback()

    await engine.dispose()
