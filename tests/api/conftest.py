import httpx
import pytest_asyncio
from fastapi import FastAPI

from app.application.ports.unit_of_work_factory import UnitOfWorkFactory
from app.bootstrap.application import Application
from app.bootstrap.container import ApplicationContainer
from app.core.config import get_settings
from app.infrastructure.security import Argon2PasswordHasher


@pytest_asyncio.fixture
async def test_app(
    test_uow_factory: UnitOfWorkFactory,
) -> FastAPI:
    settings = get_settings()

    container = ApplicationContainer(
        settings=settings,
        password_hasher=Argon2PasswordHasher(),
        unit_of_work_factory=test_uow_factory,
    )

    application = Application(
        settings=settings,
        container=container,
    )

    return application.create()


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
