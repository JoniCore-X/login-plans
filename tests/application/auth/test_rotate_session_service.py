from datetime import timedelta
from uuid import UUID

import pytest

from app.application.auth.exceptions import AuthenticationError
from app.application.auth.services import RotateSessionService
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
    def __init__(self) -> None:
        self.counter = 0

    def generate(self) -> SessionCredential:
        self.counter += 1
        return SessionCredential(
            f"credential-{self.counter}",
        )

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


def rotate_service(
    uow_factory: FakeUnitOfWorkFactory,
    credential_generator: FakeSessionCredentialGenerator,
    clock: FixedClock,
) -> RotateSessionService:
    return RotateSessionService(
        unit_of_work_factory=uow_factory,
        credential_generator=credential_generator,
        clock=clock,
    )


@pytest.mark.asyncio
async def test_rotation_creates_new_session_in_same_family() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    credential_generator = FakeSessionCredentialGenerator()
    clock = FixedClock()

    service = rotate_service(
        uow_factory,
        credential_generator,
        clock,
    )

    user = user_factory()
    await uow_factory.unit_of_work.users.add(user)

    original = session_factory(
        user_id=user.id.value,
        credential_hash="hash:old-credential",
        created_at=clock.current,
        expires_at=clock.current + timedelta(hours=24),
    )
    uow_factory.unit_of_work.sessions.sessions.append(original)

    result = await service.execute("old-credential")

    assert result.credential == "credential-1"
    assert result.user_id == user.id.value
    assert result.session_id != original.id.value

    assert original.status == SessionStatus.ROTATED
    assert original.revoked_at == clock.current

    sessions = uow_factory.unit_of_work.sessions.sessions

    assert len(sessions) == 2

    new_session = sessions[1]

    assert new_session.family_id == original.family_id
    assert new_session.status == SessionStatus.ACTIVE
    assert new_session.expires_at == original.expires_at
    assert new_session.credential_hash.value == "hash:credential-1"
    assert uow_factory.unit_of_work.committed is True


@pytest.mark.asyncio
async def test_rotation_replay_revokes_entire_family() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    credential_generator = FakeSessionCredentialGenerator()
    clock = FixedClock()

    service = rotate_service(
        uow_factory,
        credential_generator,
        clock,
    )

    user = user_factory()
    await uow_factory.unit_of_work.users.add(user)

    original = session_factory(
        user_id=user.id.value,
        credential_hash="hash:old-credential",
        created_at=clock.current,
        expires_at=clock.current + timedelta(hours=24),
    )
    uow_factory.unit_of_work.sessions.sessions.append(original)

    await service.execute("old-credential")

    with pytest.raises(AuthenticationError):
        await service.execute("old-credential")

    sessions = uow_factory.unit_of_work.sessions.sessions

    assert all(session.status == SessionStatus.REVOKED for session in sessions)


@pytest.mark.asyncio
async def test_rotation_with_unknown_credential_fails() -> None:
    service = rotate_service(
        FakeUnitOfWorkFactory(),
        FakeSessionCredentialGenerator(),
        FixedClock(),
    )

    with pytest.raises(AuthenticationError):
        await service.execute("unknown")


@pytest.mark.asyncio
async def test_rotation_expired_session_fails() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    credential_generator = FakeSessionCredentialGenerator()
    clock = FixedClock()

    service = rotate_service(
        uow_factory,
        credential_generator,
        clock,
    )

    user = user_factory()
    await uow_factory.unit_of_work.users.add(user)

    expired = session_factory(
        user_id=user.id.value,
        credential_hash="hash:old-credential",
        created_at=clock.current - timedelta(hours=2),
        expires_at=clock.current - timedelta(hours=1),
    )
    uow_factory.unit_of_work.sessions.sessions.append(expired)

    with pytest.raises(AuthenticationError):
        await service.execute("old-credential")
