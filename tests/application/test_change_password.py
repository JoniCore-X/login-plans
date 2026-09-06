from uuid import uuid4

import pytest

from app.application.auth.services import ChangePasswordService
from app.application.ports.password_hasher import PasswordHasher
from app.application.users.commands import ChangePasswordCommand
from app.application.users.exceptions import InvalidCredentialsError
from app.domain.sessions.enums import SessionStatus
from app.domain.users.value_objects import (
    PasswordHash,
    PlainPassword,
    UserId,
)
from tests.factories import FixedClock, session_factory, user_factory
from tests.fakes.plans import FakePlanRepository


class FakeUserRepository:
    def __init__(self) -> None:
        self.users: list = []

    async def get_by_id(self, user_id: UserId):
        for user in self.users:
            if user.id == user_id:
                return user
        return None

    async def get_by_email(self, email):
        for user in self.users:
            if user.email == email:
                return user
        return None

    async def add(self, user) -> None:
        self.users.append(user)

    async def update(self, user) -> None:
        for index, existing in enumerate(self.users):
            if existing.id == user.id:
                self.users[index] = user
                return


class FakeSessionRepository:
    def __init__(self) -> None:
        self.sessions: list = []

    async def get_by_id(self, session_id):
        for session in self.sessions:
            if session.id == session_id:
                return session
        return None

    async def get_by_user_id(self, user_id: UserId):
        return [s for s in self.sessions if s.user_id == user_id]

    async def get_by_credential_hash(self, credential_hash):
        for session in self.sessions:
            if session.credential_hash == credential_hash:
                return session
        return None

    async def get_by_family_id(self, family_id):
        return [s for s in self.sessions if s.family_id == family_id]

    async def add(self, session) -> None:
        self.sessions.append(session)

    async def update(self, session) -> None:
        for index, existing in enumerate(self.sessions):
            if existing.id == session.id:
                self.sessions[index] = session
                return

    async def revoke(self, session) -> None:
        await self.update(session)


class FakePasswordHasher(PasswordHasher):
    def hash(self, password: PlainPassword) -> PasswordHash:
        return PasswordHash(f"hashed:{password.value}")

    def verify(
        self,
        password: PlainPassword,
        password_hash: PasswordHash,
    ) -> bool:
        return password_hash.value == f"hashed:{password.value}"

    def needs_rehash(self, password_hash: PasswordHash) -> bool:
        return False


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.users = FakeUserRepository()
        self.sessions = FakeSessionRepository()
        self.plans = FakePlanRepository()
        self.events: list = []

    def collect_event(self, event: object) -> None:
        self.events.append(event)

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(self, *args: object) -> None:
        pass


class FakeUnitOfWorkFactory:
    def __init__(self) -> None:
        self.unit_of_work = FakeUnitOfWork()

    def create(self) -> FakeUnitOfWork:
        return self.unit_of_work


@pytest.mark.asyncio
async def test_change_password_success() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    service = ChangePasswordService(
        unit_of_work_factory=uow_factory,  # type: ignore[arg-type]
        password_hasher=FakePasswordHasher(),
        clock=FixedClock(),
    )

    user = user_factory(password_hash="hashed:old-password-1")
    uow_factory.unit_of_work.users.users.append(user)

    current_session = session_factory(user_id=user.id.value)
    other_session = session_factory(user_id=user.id.value)
    uow_factory.unit_of_work.sessions.sessions.extend(
        [current_session, other_session],
    )

    await service.execute(
        ChangePasswordCommand(
            user_id=user.id.value,
            session_id=current_session.id.value,
            current_password="old-password-1",
            new_password="NewStr0ng!Pass2026",
        ),
    )

    assert user.password_hash.value == "hashed:NewStr0ng!Pass2026"
    assert current_session.status == SessionStatus.ACTIVE
    assert other_session.status == SessionStatus.REVOKED

    event_types = [e.event_type for e in uow_factory.unit_of_work.events]
    assert "PasswordChanged" in event_types
    assert "SessionRevoked" in event_types


@pytest.mark.asyncio
async def test_change_password_wrong_current_rejected() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    service = ChangePasswordService(
        unit_of_work_factory=uow_factory,  # type: ignore[arg-type]
        password_hasher=FakePasswordHasher(),
        clock=FixedClock(),
    )

    user = user_factory(password_hash="hashed:correct-password-1")
    uow_factory.unit_of_work.users.users.append(user)

    with pytest.raises(InvalidCredentialsError):
        await service.execute(
            ChangePasswordCommand(
                user_id=user.id.value,
                session_id=uuid4(),
                current_password="wrong-password-1",
                new_password="NewStr0ng!Pass2026",
            ),
        )


@pytest.mark.asyncio
async def test_change_password_unknown_user_rejected() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    service = ChangePasswordService(
        unit_of_work_factory=uow_factory,  # type: ignore[arg-type]
        password_hasher=FakePasswordHasher(),
        clock=FixedClock(),
    )

    with pytest.raises(InvalidCredentialsError):
        await service.execute(
            ChangePasswordCommand(
                user_id=uuid4(),
                session_id=uuid4(),
                current_password="old-password-1",
                new_password="NewStr0ng!Pass2026",
            ),
        )
