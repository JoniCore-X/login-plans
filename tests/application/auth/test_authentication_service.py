from datetime import timedelta
from uuid import UUID

import pytest

from app.application.auth.exceptions import AuthenticationError
from app.application.auth.services import AuthenticationService
from app.application.ports.session_credentials import (
    SessionCredentialGenerator,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.sessions.ports import SessionRepository
from app.application.users.ports import UserRepository
from app.domain.sessions.entities import Session
from app.domain.sessions.enums import SessionStatus
from app.domain.sessions.value_objects import (
    SessionCredential,
    SessionCredentialHash,
    SessionId,
)
from app.domain.users.entities import User
from app.domain.users.enums import UserStatus
from app.domain.users.value_objects import Email, UserId
from tests.factories import FixedClock, session_factory, user_factory
from tests.fakes.plans import FakePlanRepository


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

    async def get_by_family_id(
        self,
        family_id: UUID,
    ) -> list[Session]:
        return [session for session in self.sessions if session.family_id == family_id]

    async def add(self, session: Session) -> None:
        self.sessions.append(session)

    async def update(self, session: Session) -> None:
        for index, existing in enumerate(self.sessions):
            if existing.id == session.id:
                self.sessions[index] = session
                return

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


class FakeSessionCredentialGenerator(SessionCredentialGenerator):
    def generate(self) -> SessionCredential:
        return SessionCredential("generated-credential")

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


def authentication_service(
    unit_of_work_factory: FakeUnitOfWorkFactory,
    clock: FixedClock,
) -> AuthenticationService:
    return AuthenticationService(
        unit_of_work_factory=unit_of_work_factory,
        credential_generator=FakeSessionCredentialGenerator(),
        clock=clock,
    )


def seed_session(
    uow: FakeUnitOfWork,
    user: User,
    credential: str = "valid-credential",
    **kwargs: object,
) -> Session:
    session = session_factory(
        user_id=user.id.value,
        credential_hash=f"hash:{credential}",
        **kwargs,  # type: ignore[arg-type]
    )
    uow.sessions.sessions.append(session)
    return session


@pytest.mark.asyncio
async def test_authenticate_valid_credential() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    clock = FixedClock()
    service = authentication_service(uow_factory, clock)

    user = user_factory(email="user@example.com")
    await uow_factory.unit_of_work.users.add(user)

    session = seed_session(
        uow_factory.unit_of_work,
        user,
        created_at=clock.current,
        expires_at=clock.current + timedelta(hours=24),
    )

    result = await service.authenticate("valid-credential")

    assert result.user_id == user.id.value
    assert result.session_id == session.id.value


@pytest.mark.asyncio
async def test_authenticate_unknown_credential_fails() -> None:
    service = authentication_service(
        FakeUnitOfWorkFactory(),
        FixedClock(),
    )

    with pytest.raises(AuthenticationError):
        await service.authenticate("unknown")


@pytest.mark.asyncio
async def test_authenticate_expired_session_fails() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    clock = FixedClock()
    service = authentication_service(uow_factory, clock)

    user = user_factory()
    await uow_factory.unit_of_work.users.add(user)

    seed_session(
        uow_factory.unit_of_work,
        user,
        created_at=clock.current - timedelta(hours=25),
        expires_at=clock.current - timedelta(hours=1),
    )

    with pytest.raises(AuthenticationError):
        await service.authenticate("valid-credential")


@pytest.mark.asyncio
async def test_authenticate_session_at_exact_expiry_fails() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    clock = FixedClock()
    service = authentication_service(uow_factory, clock)

    user = user_factory()
    await uow_factory.unit_of_work.users.add(user)

    seed_session(
        uow_factory.unit_of_work,
        user,
        created_at=clock.current - timedelta(hours=24),
        expires_at=clock.current,
    )

    with pytest.raises(AuthenticationError):
        await service.authenticate("valid-credential")


@pytest.mark.asyncio
async def test_authenticate_revoked_session_fails() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    clock = FixedClock()
    service = authentication_service(uow_factory, clock)

    user = user_factory()
    await uow_factory.unit_of_work.users.add(user)

    seed_session(
        uow_factory.unit_of_work,
        user,
        status=SessionStatus.REVOKED,
        created_at=clock.current,
        expires_at=clock.current + timedelta(hours=1),
    )

    with pytest.raises(AuthenticationError):
        await service.authenticate("valid-credential")


@pytest.mark.asyncio
async def test_authenticate_missing_user_fails() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    clock = FixedClock()
    service = authentication_service(uow_factory, clock)

    seed_session(
        uow_factory.unit_of_work,
        user_factory(),
        created_at=clock.current,
        expires_at=clock.current + timedelta(hours=1),
    )

    with pytest.raises(AuthenticationError):
        await service.authenticate("valid-credential")


@pytest.mark.asyncio
async def test_authenticate_suspended_user_fails() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    clock = FixedClock()
    service = authentication_service(uow_factory, clock)

    user = user_factory(status=UserStatus.SUSPENDED)
    await uow_factory.unit_of_work.users.add(user)

    seed_session(
        uow_factory.unit_of_work,
        user,
        created_at=clock.current,
        expires_at=clock.current + timedelta(hours=1),
    )

    with pytest.raises(AuthenticationError):
        await service.authenticate("valid-credential")


@pytest.mark.asyncio
async def test_credential_maps_to_correct_user() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    clock = FixedClock()
    service = authentication_service(uow_factory, clock)

    user_a = user_factory(email="a@example.com")
    user_b = user_factory(email="b@example.com")
    await uow_factory.unit_of_work.users.add(user_a)
    await uow_factory.unit_of_work.users.add(user_b)

    seed_session(
        uow_factory.unit_of_work,
        user_a,
        credential="credential-a",
        created_at=clock.current,
        expires_at=clock.current + timedelta(hours=1),
    )
    seed_session(
        uow_factory.unit_of_work,
        user_b,
        credential="credential-b",
        created_at=clock.current,
        expires_at=clock.current + timedelta(hours=1),
    )

    result_a = await service.authenticate("credential-a")
    result_b = await service.authenticate("credential-b")

    assert result_a.user_id == user_a.id.value
    assert result_b.user_id == user_b.id.value
    assert result_a.user_id != result_b.user_id


@pytest.mark.asyncio
async def test_authenticate_empty_credential_fails() -> None:
    service = authentication_service(
        FakeUnitOfWorkFactory(),
        FixedClock(),
    )

    with pytest.raises(AuthenticationError):
        await service.authenticate("")
