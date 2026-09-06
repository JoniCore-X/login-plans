from uuid import UUID

import pytest

from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.session_credentials import (
    SessionCredentialGenerator,
)
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
from app.domain.sessions.value_objects import (
    SessionCredential,
    SessionCredentialHash,
    SessionId,
)
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
from tests.fakes.plans import FakePlanRepository


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

    async def update(self, user: User) -> None:
        for index, existing in enumerate(self.users):
            if existing.id == user.id:
                self.users[index] = user
                return


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

    async def get_by_family_id(
        self,
        family_id: UUID,
    ) -> list[Session]:
        return [session for session in self.sessions if session.family_id == family_id]

    async def add(self, session: Session) -> None:
        self.sessions.append(session)

    async def update(self, session: Session) -> None:
        return None

    async def revoke(self, session: Session) -> None:
        return None


class FakeUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.users = FakeUserRepository()
        self.sessions = FakeSessionRepository()
        self.plans = FakePlanRepository()
        self.events: list = []
        self.committed = False
        self.rolled_back = False

    def collect_event(self, event: object) -> None:
        self.events.append(event)

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


class FakeSessionCredentialGenerator(SessionCredentialGenerator):
    def generate(self) -> SessionCredential:
        return SessionCredential("test-credential")

    def hash(
        self,
        credential: SessionCredential,
    ) -> SessionCredentialHash:
        return SessionCredentialHash(
            f"hash:{credential.value}",
        )

    def verify(
        self,
        credential: SessionCredential,
        credential_hash: SessionCredentialHash,
    ) -> bool:
        return credential_hash.value == (f"hash:{credential.value}")


def login_user_service(
    unit_of_work_factory: FakeUnitOfWorkFactory,
    password_hasher: FakePasswordHasher,
    clock: FixedClock,
    credential_generator: FakeSessionCredentialGenerator | None = None,
) -> LoginUserService:
    return LoginUserService(
        unit_of_work_factory=unit_of_work_factory,
        password_hasher=password_hasher,
        clock=clock,
        credential_generator=credential_generator or FakeSessionCredentialGenerator(),
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
        password_hash="hashed:valid-password-1",
    )

    await unit_of_work_factory.unit_of_work.users.add(user)

    result = await service.execute(
        LoginUserCommand(
            email="USER@example.com",
            password="valid-password-1",
        ),
    )

    assert result.user_id == user.id.value
    assert result.credential == "test-credential"
    assert result.expires_at > clock.current
    assert unit_of_work_factory.unit_of_work.committed is True
    assert len(unit_of_work_factory.unit_of_work.sessions.sessions) == 1

    session = unit_of_work_factory.unit_of_work.sessions.sessions[0]

    assert session.id.value == result.session_id
    assert session.user_id == user.id
    assert session.credential_hash.value == "hash:test-credential"
    assert session.credential_hash.value != result.credential


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
                password="valid-password-1",
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
        password_hash="hashed:correct-password-1",
    )

    await unit_of_work_factory.unit_of_work.users.add(user)

    with pytest.raises(InvalidCredentialsError):
        await service.execute(
            LoginUserCommand(
                email="user@example.com",
                password="wrong-password-1",
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
        password_hash="hashed:valid-password-1",
        status=UserStatus.SUSPENDED,
    )

    await unit_of_work_factory.unit_of_work.users.add(user)

    with pytest.raises(UserCannotAuthenticateError):
        await service.execute(
            LoginUserCommand(
                email="user@example.com",
                password="valid-password-1",
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
        password_hash="hashed:valid-password-1",
    )

    await unit_of_work_factory.unit_of_work.users.add(user)

    await service.execute(
        LoginUserCommand(
            email="user@example.com",
            password="valid-password-1",
        ),
    )

    updated_user = await unit_of_work_factory.unit_of_work.users.get_by_email(
        Email("user@example.com"),
    )

    assert updated_user is not None
    assert updated_user.updated_at == clock.current
    assert password_hasher.hashed_password is not None
    assert password_hasher.hashed_password.value == "valid-password-1"
