import httpx
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from tests.factories import TestApplicationFactory


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
