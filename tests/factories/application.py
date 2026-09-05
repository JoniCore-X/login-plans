from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.application import Application
from app.bootstrap.container import ApplicationContainer
from app.core.config import Settings
from app.infrastructure.security import Argon2PasswordHasher
from app.infrastructure.unit_of_work_factory import (
    SqlAlchemyUnitOfWorkFactory,
)


class TestApplicationFactory:
    __test__ = False

    def __init__(
        self,
        settings: Settings,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory

    def create(self) -> FastAPI:
        unit_of_work_factory = SqlAlchemyUnitOfWorkFactory(
            self.session_factory,
        )

        container = ApplicationContainer(
            settings=self.settings,
            password_hasher=Argon2PasswordHasher(),
            unit_of_work_factory=unit_of_work_factory,
        )

        application = Application(
            settings=self.settings,
            container=container,
        )

        return application.create()
