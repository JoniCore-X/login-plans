from uuid import UUID

import pytest

from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.unit_of_work import UnitOfWork
from app.application.sessions.ports import SessionRepository
from app.application.users.ports import UserRepository
from app.application.users.services import RegisterUserService
from app.domain.sessions.entities import Session
from app.domain.sessions.value_objects import (
    SessionCredentialHash,
    SessionId,
)
from app.domain.users.entities import User
from app.domain.users.exceptions import UserAlreadyExistsError
from app.domain.users.value_objects import (
    Email,
    PasswordHash,
    PlainPassword,
    UserId,
)
from tests.factories import FixedClock, registration_scenario_factory


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self.users: list[User] = []

    async def add(self, user: User) -> None:
        self.users.append(user)

    async def get_by_id(
        self,
        user_id: UserId,
    ) -> User | None:
        for user in self.users:
            if user.id == user_id:
                return user

        return None

    async def get_by_email(
        self,
        email: Email,
    ) -> User | None:
        for user in self.users:
            if user.email == email:
                return user

        return None


class FakeSessionRepository(SessionRepository):
    def __init__(self) -> None:
        self.sessions: list[Session] = []

    async def get_by_id(
        self,
        session_id: SessionId,
    ) -> Session | None:
        for session in self.sessions:
            if session.id == session_id:
                return session

        return None

    async def get_by_user_id(
        self,
        user_id: UserId,
    ) -> list[Session]:
        return [session for session in self.sessions if session.user_id == user_id]

    async def get_by_credential_hash(
        self,
        credential_hash: SessionCredentialHash,
    ) -> Session | None:
        for session in self.sessions:
            if session.credential_hash == credential_hash:
                return session

        return None

    async def add(self, session: Session) -> None:
        self.sessions.append(session)

    async def revoke(self, session: Session) -> None:
        return None


class FakeUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.users = FakeUserRepository()
        self.sessions = FakeSessionRepository()
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
    def __init__(self) -> None:
        self.hashed_password: PlainPassword | None = None

    def hash(
        self,
        password: PlainPassword,
    ) -> PasswordHash:
        self.hashed_password = password

        return PasswordHash(
            f"hashed:{password.value}",
        )

    def verify(
        self,
        password: PlainPassword,
        password_hash: PasswordHash,
    ) -> bool:
        return password_hash.value == (f"hashed:{password.value}")

    def needs_rehash(
        self,
        password_hash: PasswordHash,
    ) -> bool:
        return False


@pytest.mark.asyncio
async def test_register_user() -> None:
    unit_of_work_factory = FakeUnitOfWorkFactory()
    password_hasher = FakePasswordHasher()
    clock = FixedClock()

    service = RegisterUserService(
        unit_of_work_factory=unit_of_work_factory,
        password_hasher=password_hasher,
        clock=clock,
    )

    scenario = registration_scenario_factory(
        email="USER@example.com",
        password="secret",
    )

    result = await service.execute(
        scenario.command,
    )

    assert result.email == scenario.email.value
    assert isinstance(result.id, UUID)
    assert unit_of_work_factory.unit_of_work.committed is True
    assert len(unit_of_work_factory.unit_of_work.users.users) == 1

    created_user = unit_of_work_factory.unit_of_work.users.users[0]

    assert created_user.id.value == result.id
    assert created_user.password_hash.value == (f"hashed:{scenario.password.value}")
    assert created_user.created_at == clock.current
    assert created_user.updated_at == clock.current
    assert password_hasher.hashed_password == scenario.password


@pytest.mark.asyncio
async def test_register_user_rejects_duplicate_email() -> None:
    unit_of_work_factory = FakeUnitOfWorkFactory()
    password_hasher = FakePasswordHasher()

    service = RegisterUserService(
        unit_of_work_factory=unit_of_work_factory,
        password_hasher=password_hasher,
        clock=FixedClock(),
    )

    scenario = registration_scenario_factory(
        email="user@example.com",
        password="secret",
    )

    await service.execute(scenario.command)

    with pytest.raises(UserAlreadyExistsError):
        await service.execute(scenario.command)
