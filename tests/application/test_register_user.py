from uuid import UUID

import pytest

from app.application.commands.register_user import RegisterUserCommand
from app.application.ports.password_hasher import PasswordHasher
from app.application.services.register_user import RegisterUserService
from app.domain.entities.user import User
from app.domain.exceptions.user import UserAlreadyExistsError
from app.domain.repositories.unit_of_work import UnitOfWork
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.password import PlainPassword
from app.domain.value_objects.password_hash import PasswordHash


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self.users: list[User] = []

    async def add(self, user: User) -> None:
        self.users.append(user)

    async def get_by_id(
        self,
        user_id: UUID,
    ) -> User | None:
        for user in self.users:
            if user.id == user_id:
                return user

        return None

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        for user in self.users:
            if user.email.value == email:
                return user

        return None

    async def exists_by_email(
        self,
        email: str,
    ) -> bool:
        return any(user.email.value == email for user in self.users)


class FakeUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.users = FakeUserRepository()
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        if exc_type is not None:
            self.rolled_back = True
            return

        self.committed = True


class FakeUnitOfWorkFactory:
    def __init__(self) -> None:
        self.unit_of_work = FakeUnitOfWork()

    def create(self) -> FakeUnitOfWork:
        return self.unit_of_work


class FakePasswordHasher(PasswordHasher):
    def hash(
        self,
        password: PlainPassword,
    ) -> PasswordHash:
        return PasswordHash(
            f"hashed:{password.value}",
        )

    def verify(
        self,
        password: PlainPassword,
        password_hash: PasswordHash,
    ) -> bool:
        return password_hash.value == (f"hashed:{password.value}")


@pytest.mark.asyncio
async def test_register_user() -> None:
    unit_of_work_factory = FakeUnitOfWorkFactory()
    password_hasher = FakePasswordHasher()

    service = RegisterUserService(
        unit_of_work_factory=unit_of_work_factory,
        password_hasher=password_hasher,
    )

    result = await service.execute(
        RegisterUserCommand(
            email="USER@example.com",
            password="secret",
        ),
    )

    assert result.email == "user@example.com"
    assert isinstance(result.id, UUID)
    assert unit_of_work_factory.unit_of_work.committed is True
    assert len(unit_of_work_factory.unit_of_work.users.users) == 1


@pytest.mark.asyncio
async def test_register_user_rejects_duplicate_email() -> None:
    unit_of_work_factory = FakeUnitOfWorkFactory()
    password_hasher = FakePasswordHasher()

    service = RegisterUserService(
        unit_of_work_factory=unit_of_work_factory,
        password_hasher=password_hasher,
    )

    command = RegisterUserCommand(
        email="user@example.com",
        password="secret",
    )

    await service.execute(command)

    with pytest.raises(UserAlreadyExistsError):
        await service.execute(command)
