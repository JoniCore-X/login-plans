import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import router
from app.application.ports.password_hasher import PasswordHasher
from app.bootstrap.container import ApplicationContainer
from app.core.config import Settings
from app.core.logging import configure_logging
from app.infrastructure.security import Argon2PasswordHasher

logger = logging.getLogger(__name__)


class Application:
    def __init__(
        self,
        settings: Settings,
    ) -> None:
        self.settings = settings

        password_hasher: PasswordHasher = Argon2PasswordHasher()

        self.container = ApplicationContainer(
            settings=settings,
            password_hasher=password_hasher,
        )

    def create(self) -> FastAPI:
        configure_logging(
            self.settings.debug,
        )

        @asynccontextmanager
        async def lifespan(
            application: FastAPI,
        ) -> AsyncIterator[None]:
            logger.info("Application startup")

            yield

            logger.info("Application shutdown")

            await self.container.database.dispose()

        application = FastAPI(
            title=self.settings.app_name,
            debug=self.settings.debug,
            lifespan=lifespan,
        )

        application.state.container = self.container

        application.include_router(router)

        logger.info(
            "Application created: %s",
            self.settings.app_name,
        )

        return application
