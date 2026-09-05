from app.application.ports.clock import Clock
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.session_credentials import (
    SessionCredentialGenerator,
)
from app.application.ports.unit_of_work_factory import UnitOfWorkFactory
from app.application.users.services import (
    GetUserService,
    LoginUserService,
    RegisterUserService,
)
from app.core.config import Settings
from app.infrastructure.clock import SystemClock
from app.infrastructure.database import Database
from app.infrastructure.security.session_credentials import (
    SecureSessionCredentialGenerator,
)
from app.infrastructure.unit_of_work_factory import (
    SqlAlchemyUnitOfWorkFactory,
)


class ApplicationContainer:
    def __init__(
        self,
        settings: Settings,
        password_hasher: PasswordHasher,
        unit_of_work_factory: UnitOfWorkFactory | None = None,
        clock: Clock | None = None,
        credential_generator: SessionCredentialGenerator | None = None,
    ) -> None:
        self.settings = settings
        self.database = Database(settings)

        if unit_of_work_factory is None:
            unit_of_work_factory = SqlAlchemyUnitOfWorkFactory(
                self.database.session_factory,
            )

        if clock is None:
            clock = SystemClock()

        if credential_generator is None:
            credential_generator = SecureSessionCredentialGenerator()

        self.unit_of_work_factory = unit_of_work_factory
        self.password_hasher = password_hasher
        self.clock = clock
        self.credential_generator = credential_generator

    def create_register_user_service(
        self,
    ) -> RegisterUserService:
        return RegisterUserService(
            unit_of_work_factory=self.unit_of_work_factory,
            password_hasher=self.password_hasher,
            clock=self.clock,
        )

    def create_login_user_service(
        self,
    ) -> LoginUserService:
        return LoginUserService(
            unit_of_work_factory=self.unit_of_work_factory,
            password_hasher=self.password_hasher,
            clock=self.clock,
            credential_generator=self.credential_generator,
        )

    def create_get_user_service(
        self,
    ) -> GetUserService:
        return GetUserService(
            unit_of_work_factory=self.unit_of_work_factory,
        )


def create_container(
    settings: Settings,
    password_hasher: PasswordHasher,
    unit_of_work_factory: UnitOfWorkFactory | None = None,
    clock: Clock | None = None,
    credential_generator: SessionCredentialGenerator | None = None,
) -> ApplicationContainer:
    return ApplicationContainer(
        settings=settings,
        password_hasher=password_hasher,
        unit_of_work_factory=unit_of_work_factory,
        clock=clock,
        credential_generator=credential_generator,
    )
