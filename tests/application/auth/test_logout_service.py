from datetime import timedelta
from uuid import UUID

import pytest

from app.application.auth.exceptions import AuthenticationError
from app.application.auth.services import LogoutService
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
from app.domain.users.value_objects import Email, UserId
from tests.factories import FixedClock, session_factory, user_factory
from tests.fakes.plans import FakePlanRepository


class FakeUserRepository(UserRepository):
    def __init__(self) -> None:
        self.users: list[User] = []

    async def add(self, user: User) -> None:
        self.users.append(user)

    async def get_by_id(self, user_id: UserId) -> User | None:
        for user in self.users:
            if user.id == user_id:
                return user

        return None

    async def get_by_email(self, email: Email) -> User | None:
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


@pytest.mark.asyncio
async def test_logout_revokes_session() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    clock = FixedClock()

    service = LogoutService(
        unit_of_work_factory=uow_factory,
        credential_generator=FakeSessionCredentialGenerator(),
        clock=clock,
    )

    user = user_factory()
    await uow_factory.unit_of_work.users.add(user)

    session = session_factory(
        user_id=user.id.value,
        credential_hash="hash:my-credential",
        created_at=clock.current,
        expires_at=clock.current + timedelta(hours=1),
    )
    uow_factory.unit_of_work.sessions.sessions.append(session)

    await service.execute("my-credential")

    assert session.status == SessionStatus.REVOKED
    assert session.revoked_at == clock.current
    assert uow_factory.unit_of_work.committed is True


@pytest.mark.asyncio
async def test_logout_unknown_credential_fails() -> None:
    service = LogoutService(
        unit_of_work_factory=FakeUnitOfWorkFactory(),
        credential_generator=FakeSessionCredentialGenerator(),
        clock=FixedClock(),
    )

    with pytest.raises(AuthenticationError):
        await service.execute("unknown")


@pytest.mark.asyncio
async def test_logout_already_revoked_session_fails() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    clock = FixedClock()

    service = LogoutService(
        unit_of_work_factory=uow_factory,
        credential_generator=FakeSessionCredentialGenerator(),
        clock=clock,
    )

    session = session_factory(
        credential_hash="hash:my-credential",
        status=SessionStatus.REVOKED,
        created_at=clock.current,
        expires_at=clock.current + timedelta(hours=1),
    )
    uow_factory.unit_of_work.sessions.sessions.append(session)

    with pytest.raises(AuthenticationError):
        await service.execute("my-credential")


@pytest.mark.asyncio
async def test_logout_expired_session_fails() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    clock = FixedClock()

    service = LogoutService(
        unit_of_work_factory=uow_factory,
        credential_generator=FakeSessionCredentialGenerator(),
        clock=clock,
    )

    session = session_factory(
        credential_hash="hash:my-credential",
        created_at=clock.current - timedelta(hours=2),
        expires_at=clock.current - timedelta(hours=1),
    )
    uow_factory.unit_of_work.sessions.sessions.append(session)

    with pytest.raises(AuthenticationError):
        await service.execute("my-credential")
