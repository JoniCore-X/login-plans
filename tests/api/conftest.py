import httpx
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_register_user_service
from app.application.services.register_user import RegisterUserService
from app.infrastructure.security import Argon2PasswordHasher
from app.main import app
from tests.infrastructure.database import TestUnitOfWorkFactory


@pytest_asyncio.fixture
async def client(
    test_session: AsyncSession,
) -> httpx.AsyncClient:
    service = RegisterUserService(
        unit_of_work_factory=TestUnitOfWorkFactory(
            test_session,
        ),
        password_hasher=Argon2PasswordHasher(),
    )

    app.dependency_overrides[get_register_user_service] = lambda: service

    transport = httpx.ASGITransport(
        app=app,
    )

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()
