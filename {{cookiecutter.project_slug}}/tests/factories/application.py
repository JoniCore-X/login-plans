from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.ports.email_sender import EmailSender
from app.application.ports.health_checker import HealthChecker
from app.application.ports.rate_limiter import RateLimiter
from app.bootstrap.application import Application
from app.bootstrap.container import ApplicationContainer
from app.core.config import Settings
from app.infrastructure.events.audit_log_dispatcher import (
    AuditLogDispatcher,
)
from app.infrastructure.security import Argon2PasswordHasher
from app.infrastructure.unit_of_work_factory import (
    SqlAlchemyUnitOfWorkFactory,
)
from tests.fakes.email import FakeEmailSender


class TestApplicationFactory:
    __test__ = False

    def __init__(
        self,
        settings: Settings,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.settings = settings
        self.session_factory = session_factory
        self.email_sender = FakeEmailSender()

    def create(
        self,
        *,
        rate_limiter: RateLimiter | None = None,
        health_checker: HealthChecker | None = None,
        email_sender: EmailSender | None = None,
    ) -> FastAPI:
        unit_of_work_factory = SqlAlchemyUnitOfWorkFactory(
            self.session_factory,
            AuditLogDispatcher(self.session_factory),
        )

        container = ApplicationContainer(
            settings=self.settings,
            password_hasher=Argon2PasswordHasher(),
            unit_of_work_factory=unit_of_work_factory,
            rate_limiter=rate_limiter,
            health_checker=health_checker,
            email_sender=email_sender or self.email_sender,
        )

        application = Application(
            settings=self.settings,
            container=container,
        )

        return application.create()
