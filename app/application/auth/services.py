from uuid import uuid4

from app.application.auth.dto import AuthenticatedUser
from app.application.auth.exceptions import AuthenticationError
from app.application.ports.clock import Clock
from app.application.ports.session_credentials import (
    SessionCredentialGenerator,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.ports.unit_of_work_factory import UnitOfWorkFactory
from app.application.users.dto import AuthenticationDTO
from app.domain.sessions.entities import Session
from app.domain.sessions.value_objects import SessionCredential


class AuthenticationService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        credential_generator: SessionCredentialGenerator,
        clock: Clock,
    ) -> None:
        self.unit_of_work_factory = unit_of_work_factory
        self.credential_generator = credential_generator
        self.clock = clock

    async def authenticate(
        self,
        credential: str,
    ) -> AuthenticatedUser:
        if not credential:
            raise AuthenticationError(
                "Authentication failed.",
            )

        session_credential = SessionCredential(credential)
        credential_hash = self.credential_generator.hash(
            session_credential,
        )

        unit_of_work = self.unit_of_work_factory.create()

        async with unit_of_work:
            session = await unit_of_work.sessions.get_by_credential_hash(
                credential_hash,
            )

            if session is None:
                raise AuthenticationError(
                    "Authentication failed.",
                )

            if session.was_rotated():
                await self._revoke_family(
                    unit_of_work,
                    session,
                )
            elif not session.is_active(now=self.clock.now()):
                raise AuthenticationError(
                    "Authentication failed.",
                )
            else:
                user = await unit_of_work.users.get_by_id(
                    session.user_id,
                )

                if user is None or not user.can_authenticate():
                    raise AuthenticationError(
                        "Authentication failed.",
                    )

                return AuthenticatedUser(
                    user_id=user.id.value,
                    session_id=session.id.value,
                )

        raise AuthenticationError(
            "Authentication failed.",
        )

    async def _revoke_family(
        self,
        unit_of_work: UnitOfWork,
        session: Session,
    ) -> None:
        family = await unit_of_work.sessions.get_by_family_id(
            session.family_id,
        )

        now = self.clock.now()

        for member in family:
            member.revoke(now=now)
            await unit_of_work.sessions.update(member)


class LogoutService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        credential_generator: SessionCredentialGenerator,
        clock: Clock,
    ) -> None:
        self.unit_of_work_factory = unit_of_work_factory
        self.credential_generator = credential_generator
        self.clock = clock

    async def execute(
        self,
        credential: str,
    ) -> None:
        if not credential:
            raise AuthenticationError(
                "Authentication failed.",
            )

        session_credential = SessionCredential(credential)
        credential_hash = self.credential_generator.hash(
            session_credential,
        )

        unit_of_work = self.unit_of_work_factory.create()

        async with unit_of_work:
            session = await unit_of_work.sessions.get_by_credential_hash(
                credential_hash,
            )

            now = self.clock.now()

            if session is None or not session.is_active(now=now):
                raise AuthenticationError(
                    "Authentication failed.",
                )

            session.revoke(now=now)

            await unit_of_work.sessions.revoke(session)


class RotateSessionService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        credential_generator: SessionCredentialGenerator,
        clock: Clock,
    ) -> None:
        self.unit_of_work_factory = unit_of_work_factory
        self.credential_generator = credential_generator
        self.clock = clock

    async def execute(
        self,
        credential: str,
    ) -> AuthenticationDTO:
        if not credential:
            raise AuthenticationError(
                "Authentication failed.",
            )

        session_credential = SessionCredential(credential)
        credential_hash = self.credential_generator.hash(
            session_credential,
        )

        unit_of_work = self.unit_of_work_factory.create()

        async with unit_of_work:
            session = await unit_of_work.sessions.get_by_credential_hash(
                credential_hash,
            )

            now = self.clock.now()

            if session is None:
                raise AuthenticationError(
                    "Authentication failed.",
                )

            if session.was_rotated():
                await self._revoke_family(
                    unit_of_work,
                    session,
                )
            elif not session.is_active(now=now):
                raise AuthenticationError(
                    "Authentication failed.",
                )
            else:
                user = await unit_of_work.users.get_by_id(
                    session.user_id,
                )

                if user is None or not user.can_authenticate():
                    raise AuthenticationError(
                        "Authentication failed.",
                    )

                new_credential = self.credential_generator.generate()
                new_credential_hash = self.credential_generator.hash(
                    new_credential,
                )

                session.rotate(now=now)
                await unit_of_work.sessions.update(session)

                new_session = Session.create(
                    session_id=uuid4(),
                    user_id=user.id,
                    credential_hash=new_credential_hash,
                    family_id=session.family_id,
                    now=now,
                    expires_at=session.expires_at,
                )

                await unit_of_work.sessions.add(new_session)

                return AuthenticationDTO(
                    user_id=user.id.value,
                    session_id=new_session.id.value,
                    credential=new_credential.value,
                    expires_at=new_session.expires_at,
                )

        raise AuthenticationError(
            "Authentication failed.",
        )

    async def _revoke_family(
        self,
        unit_of_work: UnitOfWork,
        session: Session,
    ) -> None:
        family = await unit_of_work.sessions.get_by_family_id(
            session.family_id,
        )

        now = self.clock.now()

        for member in family:
            member.revoke(now=now)
            await unit_of_work.sessions.update(member)
