from uuid import uuid4

from app.application.auth.dto import AuthenticatedUser
from app.application.auth.exceptions import AuthenticationError
from app.application.ports.clock import Clock
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.session_credentials import (
    SessionCredentialGenerator,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.ports.unit_of_work_factory import UnitOfWorkFactory
from app.application.users.commands import (
    ChangePasswordCommand,
    VerifyEmailCommand,
)
from app.application.users.dto import AuthenticationDTO
from app.application.users.exceptions import InvalidCredentialsError
from app.domain.events import (
    ReplayAttackDetected,
    SessionRevoked,
    SessionRotated,
)
from app.domain.sessions.entities import Session
from app.domain.sessions.value_objects import SessionCredential
from app.domain.users.exceptions import InvalidVerificationTokenError
from app.domain.users.value_objects import (
    PlainPassword,
    UserId,
    WeakPasswordError,
)


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
                unit_of_work.collect_event(
                    ReplayAttackDetected(
                        occurred_at=self.clock.now(),
                        session_id=session.id.value,
                        family_id=session.family_id,
                        user_id=session.user_id.value,
                    ),
                )

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

            unit_of_work.collect_event(
                SessionRevoked(
                    occurred_at=now,
                    session_id=session.id.value,
                    user_id=session.user_id.value,
                ),
            )


class ChangePasswordService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        password_hasher: PasswordHasher,
        clock: Clock,
    ) -> None:
        self.unit_of_work_factory = unit_of_work_factory
        self.password_hasher = password_hasher
        self.clock = clock

    async def execute(
        self,
        command: ChangePasswordCommand,
    ) -> None:
        new_password = PlainPassword(command.new_password)

        try:
            current_password = PlainPassword(command.current_password)
        except WeakPasswordError:
            raise InvalidCredentialsError(
                "Invalid credentials.",
            ) from None

        unit_of_work = self.unit_of_work_factory.create()

        async with unit_of_work:
            user = await unit_of_work.users.get_by_id(
                UserId(command.user_id),
            )

            if user is None or not user.can_authenticate():
                raise InvalidCredentialsError(
                    "Invalid credentials.",
                )

            if not self.password_hasher.verify(
                current_password,
                user.password_hash,
            ):
                raise InvalidCredentialsError(
                    "Invalid credentials.",
                )

            now = self.clock.now()

            user.change_password(
                new_hash=self.password_hasher.hash(new_password),
                now=now,
            )

            await unit_of_work.users.update(user)

            for event in user.pull_events():
                unit_of_work.collect_event(event)

            sessions = await unit_of_work.sessions.get_by_user_id(
                UserId(command.user_id),
            )

            for session in sessions:
                if session.id.value != command.session_id and session.is_active(
                    now=now
                ):
                    session.revoke(now=now)
                    await unit_of_work.sessions.update(session)

                    unit_of_work.collect_event(
                        SessionRevoked(
                            occurred_at=now,
                            session_id=session.id.value,
                            user_id=session.user_id.value,
                        ),
                    )


class VerifyEmailService:
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
        command: VerifyEmailCommand,
    ) -> None:
        token = SessionCredential(command.token)
        token_hash = self.credential_generator.hash(token)

        unit_of_work = self.unit_of_work_factory.create()

        async with unit_of_work:
            user = await unit_of_work.users.get_by_verification_token_hash(
                token_hash.value,
            )

            if user is None:
                raise InvalidVerificationTokenError(
                    "Invalid verification token.",
                )

            user.verify_email(
                token_hash=token_hash.value,
                now=self.clock.now(),
            )

            await unit_of_work.users.update(user)

            for event in user.pull_events():
                unit_of_work.collect_event(event)


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
                unit_of_work.collect_event(
                    ReplayAttackDetected(
                        occurred_at=now,
                        session_id=session.id.value,
                        family_id=session.family_id,
                        user_id=session.user_id.value,
                    ),
                )

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

                unit_of_work.collect_event(
                    SessionRotated(
                        occurred_at=now,
                        session_id=new_session.id.value,
                        family_id=session.family_id,
                        user_id=session.user_id.value,
                    ),
                )

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
