from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.unit_of_work_factory import UnitOfWorkFactory
from app.application.services.get_user import GetUserService
from app.application.services.register_user import RegisterUserService
from app.core.config import Settings
from app.infrastructure.database import Database
from app.infrastructure.unit_of_work_factory import (
    SqlAlchemyUnitOfWorkFactory,
)


class ApplicationContainer:
    def __init__(
        self,
        settings: Settings,
        password_hasher: PasswordHasher,
    ) -> None:
        self.settings = settings
        self.database = Database(settings)

        self.unit_of_work_factory: UnitOfWorkFactory = SqlAlchemyUnitOfWorkFactory(
            self.database.session_factory,
        )

        self.password_hasher = password_hasher

    def create_register_user_service(
        self,
    ) -> RegisterUserService:
        return RegisterUserService(
            unit_of_work_factory=self.unit_of_work_factory,
            password_hasher=self.password_hasher,
        )

    def create_get_user_service(self) -> GetUserService:
        return GetUserService(
            unit_of_work_factory=self.unit_of_work_factory,
        )


def create_container(
    settings: Settings,
    password_hasher: PasswordHasher,
) -> ApplicationContainer:
    return ApplicationContainer(
        settings=settings,
        password_hasher=password_hasher,
    )
