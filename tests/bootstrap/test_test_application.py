import pytest
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.infrastructure.unit_of_work_factory import (
    SqlAlchemyUnitOfWorkFactory,
)
from tests.factories import TestApplicationFactory


@pytest.mark.asyncio
async def test_test_application_factory_creates_application(
    test_settings: Settings,
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    factory = TestApplicationFactory(
        settings=test_settings,
        session_factory=test_session_factory,
    )

    app = factory.create()

    assert isinstance(app, FastAPI)


@pytest.mark.asyncio
async def test_test_application_factory_uses_test_uow(
    test_settings: Settings,
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    factory = TestApplicationFactory(
        settings=test_settings,
        session_factory=test_session_factory,
    )

    app = factory.create()

    container = app.state.container

    assert isinstance(
        container.unit_of_work_factory,
        SqlAlchemyUnitOfWorkFactory,
    )
