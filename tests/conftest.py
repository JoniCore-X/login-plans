import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from app.application.ports.unit_of_work_factory import UnitOfWorkFactory
from app.core.config import Settings, get_settings
from app.database.engine import create_database_engine
from app.infrastructure.unit_of_work_factory import (
    SqlAlchemyUnitOfWorkFactory,
)
from tests.factories import (
    RegistrationScenario,
    registration_scenario_factory,
)

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
async def test_connection(
    test_engine: AsyncEngine,
) -> AsyncConnection:
    async with test_engine.connect() as connection:
        transaction = await connection.begin()

        try:
            yield connection
        finally:
            if transaction.is_active:
                await transaction.rollback()


@pytest_asyncio.fixture
async def test_session_factory(
    test_connection: AsyncConnection,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=test_connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )


@pytest_asyncio.fixture
async def test_session(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncSession:
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def test_uow_factory(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> UnitOfWorkFactory:
    return SqlAlchemyUnitOfWorkFactory(
        test_session_factory,
    )


@pytest.fixture
def registration_scenario() -> RegistrationScenario:
    return registration_scenario_factory()


@pytest.fixture
def test_settings() -> Settings:
    return get_settings()
