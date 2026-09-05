import os

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.config import get_settings
from app.database.engine import create_database_engine
from tests.infrastructure.database import TestDatabase

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://login_plans:login_plans_dev_password@localhost:5432/login_plans_test"
)


@pytest_asyncio.fixture
async def test_engine() -> AsyncEngine:
    settings = get_settings()

    engine = create_database_engine(settings)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def test_database(
    test_engine: AsyncEngine,
) -> TestDatabase:
    database = TestDatabase(
        test_engine,
    )

    await database.start()

    yield database

    await database.stop()


@pytest_asyncio.fixture
async def test_session(
    test_database: TestDatabase,
) -> AsyncSession:
    if test_database.session is None:
        raise RuntimeError(
            "Test database session was not initialized",
        )

    return test_database.session
