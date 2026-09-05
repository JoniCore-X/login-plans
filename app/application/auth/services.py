from app.application.auth.dto import AuthenticatedUser
from app.application.auth.exceptions import AuthenticationError
from app.application.ports.clock import Clock
from app.application.ports.session_credentials import (
    SessionCredentialGenerator,
)
from app.application.ports.unit_of_work_factory import UnitOfWorkFactory
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

            if not session.is_active(now=self.clock.now()):
                raise AuthenticationError(
                    "Authentication failed.",
                )

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
