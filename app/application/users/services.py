from datetime import timedelta
from uuid import uuid4

from app.application.ports.clock import Clock
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.unit_of_work_factory import UnitOfWorkFactory
from app.application.users.commands import (
    LoginUserCommand,
    RegisterUserCommand,
)
from app.application.users.dto import AuthenticationDTO, UserDTO
from app.application.users.exceptions import (
    InvalidCredentialsError,
    UserCannotAuthenticateError,
)
from app.application.users.queries import GetUserQuery
from app.domain.sessions.entities import Session
from app.domain.users.entities import User
from app.domain.users.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.domain.users.value_objects import Email, PlainPassword

SESSION_DURATION = timedelta(hours=24)


class RegisterUserService:
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
        command: RegisterUserCommand,
    ) -> UserDTO:
        email = Email(command.email)
        password = PlainPassword(command.password)

        unit_of_work = self.unit_of_work_factory.create()

        async with unit_of_work:
            existing = await unit_of_work.users.get_by_email(
                email,
            )

            if existing is not None:
                raise UserAlreadyExistsError(
                    "A user with this email already exists",
                )

            password_hash = self.password_hasher.hash(
                password,
            )

            user = User.create(
                user_id=uuid4(),
                email=email.value,
                password_hash=password_hash.value,
                now=self.clock.now(),
            )

            await unit_of_work.users.add(user)

            return UserDTO(
                id=user.id.value,
                email=user.email.value,
                status=user.status,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )


class GetUserService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
    ) -> None:
        self.unit_of_work_factory = unit_of_work_factory

    async def execute(
        self,
        query: GetUserQuery,
    ) -> UserDTO:
        unit_of_work = self.unit_of_work_factory.create()

        async with unit_of_work:
            user = await unit_of_work.users.get_by_id(
                query.user_id,
            )

            if user is None:
                raise UserNotFoundError(
                    "User not found",
                )

            return UserDTO(
                id=user.id.value,
                email=user.email.value,
                status=user.status,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )


class LoginUserService:
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
        command: LoginUserCommand,
    ) -> AuthenticationDTO:
        email = Email(command.email)
        password = PlainPassword(command.password)

        unit_of_work = self.unit_of_work_factory.create()

        async with unit_of_work:
            user = await unit_of_work.users.get_by_email(
                email,
            )

            if user is None:
                raise InvalidCredentialsError(
                    "Invalid credentials",
                )

            if not user.can_authenticate():
                raise UserCannotAuthenticateError(
                    "User cannot authenticate",
                )

            if not self.password_hasher.verify(
                password,
                user.password_hash,
            ):
                raise InvalidCredentialsError(
                    "Invalid credentials",
                )

            now = self.clock.now()

            if self.password_hasher.needs_rehash(
                user.password_hash,
            ):
                user.password_hash = self.password_hasher.hash(
                    password,
                )
                user.updated_at = now

                await unit_of_work.users.add(user)

            session = Session.create(
                session_id=uuid4(),
                user_id=user.id,
                now=now,
                expires_at=now + SESSION_DURATION,
            )

            await unit_of_work.sessions.add(session)

            return AuthenticationDTO(
                user_id=user.id.value,
                session_id=session.id.value,
                expires_at=session.expires_at,
            )
