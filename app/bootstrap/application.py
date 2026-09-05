import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.exception_handlers import (
    authentication_error_handler,
    domain_error_handler,
    invalid_credentials_handler,
    invalid_email_handler,
    rate_limit_exceeded_handler,
    user_already_exists_handler,
    user_cannot_authenticate_handler,
    user_not_found_handler,
    weak_password_handler,
)
from app.api.router import router
from app.application.auth.exceptions import (
    AuthenticationError,
    RateLimitExceededError,
)
from app.application.ports.password_hasher import PasswordHasher
from app.application.users.exceptions import (
    InvalidCredentialsError,
    UserCannotAuthenticateError,
)
from app.bootstrap.container import ApplicationContainer
from app.core.config import Settings
from app.core.logging import configure_logging
from app.domain.exceptions.base import DomainError
from app.domain.users.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.domain.users.value_objects import (
    InvalidEmailError,
    WeakPasswordError,
)
from app.infrastructure.security import Argon2PasswordHasher

logger = logging.getLogger(__name__)


class Application:
    def __init__(
        self,
        settings: Settings,
        container: ApplicationContainer | None = None,
    ) -> None:
        self.settings = settings

        if container is None:
            password_hasher: PasswordHasher = Argon2PasswordHasher()

            container = ApplicationContainer(
                settings=settings,
                password_hasher=password_hasher,
            )

        self.container = container

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

        application.add_exception_handler(
            UserAlreadyExistsError,
            user_already_exists_handler,
        )

        application.add_exception_handler(
            UserNotFoundError,
            user_not_found_handler,
        )

        application.add_exception_handler(
            InvalidEmailError,
            invalid_email_handler,
        )

        application.add_exception_handler(
            InvalidCredentialsError,
            invalid_credentials_handler,
        )

        application.add_exception_handler(
            UserCannotAuthenticateError,
            user_cannot_authenticate_handler,
        )

        application.add_exception_handler(
            AuthenticationError,
            authentication_error_handler,
        )

        application.add_exception_handler(
            RateLimitExceededError,
            rate_limit_exceeded_handler,
        )

        application.add_exception_handler(
            WeakPasswordError,
            weak_password_handler,
        )

        application.add_exception_handler(
            DomainError,
            domain_error_handler,
        )

        application.include_router(router)

        logger.info(
            "Application created: %s",
            self.settings.app_name,
        )

        return application
