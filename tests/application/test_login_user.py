import pytest

from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.unit_of_work import UnitOfWork
from app.application.sessions.ports import SessionRepository
from app.application.users.commands import LoginUserCommand
from app.application.users.exceptions import (
    InvalidCredentialsError,
    UserCannotAuthenticateError,
)
from app.application.users.ports import UserRepository
from app.application.users.services import LoginUserService
from app.domain.sessions.entities import Session
from app.domain.sessions.value_objects import SessionId
from app.domain.users.entities import User
from app.domain.users.enums import UserStatus
from app.domain.users.value_objects import (
    Email,
    PasswordHash,
    PlainPassword,
    UserId,
)
from tests.factories import (
    FixedClock,
    user_factory,
)


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self.users: list[User] = []

    async def add(self, user: User) -> None:
        for index, existing in enumerate(self.users):
            if existing.id == user.id:
                self.users[index] = user
                return

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
    def __init__(
        self,
        needs_rehash: bool = False,
    ) -> None:
        self._needs_rehash = needs_rehash
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
        return self._needs_rehash


def login_user_service(
    unit_of_work_factory: FakeUnitOfWorkFactory,
    password_hasher: FakePasswordHasher,
    clock: FixedClock,
) -> LoginUserService:
    return LoginUserService(
        unit_of_work_factory=unit_of_work_factory,
        password_hasher=password_hasher,
        clock=clock,
    )


@pytest.mark.asyncio
async def test_login_user_creates_session() -> None:
    unit_of_work_factory = FakeUnitOfWorkFactory()
    password_hasher = FakePasswordHasher()
    clock = FixedClock()

    service = login_user_service(
        unit_of_work_factory,
        password_hasher,
        clock,
    )

    user = user_factory(
        email="user@example.com",
        password_hash="hashed:secret",
    )

    await unit_of_work_factory.unit_of_work.users.add(user)

    result = await service.execute(
        LoginUserCommand(
            email="USER@example.com",
            password="secret",
        ),
    )

    assert result.user_id == user.id.value
    assert result.expires_at > clock.current
    assert unit_of_work_factory.unit_of_work.committed is True
    assert len(unit_of_work_factory.unit_of_work.sessions.sessions) == 1

    session = unit_of_work_factory.unit_of_work.sessions.sessions[0]

    assert session.id.value == result.session_id
    assert session.user_id == user.id


@pytest.mark.asyncio
async def test_login_rejects_unknown_email() -> None:
    unit_of_work_factory = FakeUnitOfWorkFactory()
    password_hasher = FakePasswordHasher()
    clock = FixedClock()

    service = login_user_service(
        unit_of_work_factory,
        password_hasher,
        clock,
    )

    with pytest.raises(InvalidCredentialsError):
        await service.execute(
            LoginUserCommand(
                email="nobody@example.com",
                password="secret",
            ),
        )


@pytest.mark.asyncio
async def test_login_rejects_wrong_password() -> None:
    unit_of_work_factory = FakeUnitOfWorkFactory()
    password_hasher = FakePasswordHasher()
    clock = FixedClock()

    service = login_user_service(
        unit_of_work_factory,
        password_hasher,
        clock,
    )

    user = user_factory(
        email="user@example.com",
        password_hash="hashed:correct",
    )

    await unit_of_work_factory.unit_of_work.users.add(user)

    with pytest.raises(InvalidCredentialsError):
        await service.execute(
            LoginUserCommand(
                email="user@example.com",
                password="wrong",
            ),
        )


@pytest.mark.asyncio
async def test_login_rejects_suspended_user() -> None:
    unit_of_work_factory = FakeUnitOfWorkFactory()
    password_hasher = FakePasswordHasher()
    clock = FixedClock()

    service = login_user_service(
        unit_of_work_factory,
        password_hasher,
        clock,
    )

    user = user_factory(
        email="user@example.com",
        password_hash="hashed:secret",
        status=UserStatus.SUSPENDED,
    )

    await unit_of_work_factory.unit_of_work.users.add(user)

    with pytest.raises(UserCannotAuthenticateError):
        await service.execute(
            LoginUserCommand(
                email="user@example.com",
                password="secret",
            ),
        )


@pytest.mark.asyncio
async def test_login_rehashes_outdated_password_hash() -> None:
    unit_of_work_factory = FakeUnitOfWorkFactory()
    password_hasher = FakePasswordHasher(
        needs_rehash=True,
    )
    clock = FixedClock()

    service = login_user_service(
        unit_of_work_factory,
        password_hasher,
        clock,
    )

    user = user_factory(
        email="user@example.com",
        password_hash="hashed:secret",
    )

    await unit_of_work_factory.unit_of_work.users.add(user)

    await service.execute(
        LoginUserCommand(
            email="user@example.com",
            password="secret",
        ),
    )

    updated_user = await unit_of_work_factory.unit_of_work.users.get_by_email(
        Email("user@example.com"),
    )

    assert updated_user is not None
    assert updated_user.updated_at == clock.current
    assert password_hasher.hashed_password is not None
    assert password_hasher.hashed_password.value == "secret"
