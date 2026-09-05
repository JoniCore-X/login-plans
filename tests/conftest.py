import asyncio
import os

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.application.ports.unit_of_work_factory import UnitOfWorkFactory
from app.core.config import Settings, get_settings
from app.database.base import Base
from app.database.engine import create_database_engine
from app.infrastructure.unit_of_work_factory import (
    SqlAlchemyUnitOfWorkFactory,
)
from tests.factories import (
    RegistrationScenario,
    TestApplicationFactory,
    registration_scenario_factory,
)

WORKER_ID = os.environ.get("PYTEST_XDIST_WORKER")

if WORKER_ID and WORKER_ID != "master":
    TEST_DATABASE_NAME = f"login_plans_test_{WORKER_ID}"
else:
    TEST_DATABASE_NAME = "login_plans_test"

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://login_plans:login_plans_dev_password"
    f"@localhost:5432/{TEST_DATABASE_NAME}"
)

MAINTENANCE_DATABASE_URL = (
    "postgresql+asyncpg://login_plans:login_plans_dev_password@localhost:5432/postgres"
)


async def _create_database_if_missing() -> None:
    maintenance_engine = create_async_engine(
        MAINTENANCE_DATABASE_URL,
        isolation_level="AUTOCOMMIT",
    )

    try:
        async with maintenance_engine.connect() as connection:
            exists = await connection.scalar(
                text(
                    "SELECT 1 FROM pg_database WHERE datname = :name",
                ),
                {"name": TEST_DATABASE_NAME},
            )

            if not exists:
                await connection.execute(
                    text(f'CREATE DATABASE "{TEST_DATABASE_NAME}"'),
                )
    finally:
        await maintenance_engine.dispose()


async def _create_schema_if_missing() -> None:
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
    )

    try:
        async with engine.begin() as connection:
            await connection.run_sync(
                Base.metadata.create_all,
            )
    finally:
        await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def ensure_test_database() -> None:
    asyncio.run(_create_database_if_missing())
    asyncio.run(_create_schema_if_missing())


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


@pytest_asyncio.fixture
async def test_application_factory(
    test_settings: Settings,
    test_session_factory: async_sessionmaker[AsyncSession],
) -> TestApplicationFactory:
    return TestApplicationFactory(
        settings=test_settings,
        session_factory=test_session_factory,
    )


@pytest_asyncio.fixture
async def test_app(
    test_application_factory: TestApplicationFactory,
) -> FastAPI:
    return test_application_factory.create()


@pytest_asyncio.fixture
async def client(
    test_app: FastAPI,
) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(
        app=test_app,
    )

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client
