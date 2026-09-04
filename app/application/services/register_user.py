from app.application.commands.register_user import RegisterUserCommand
from app.application.dto.user import UserDTO
from app.application.ports.password_hasher import PasswordHasher
from app.application.ports.unit_of_work_factory import UnitOfWorkFactory
from app.domain.entities.user import User
from app.domain.exceptions.user import UserAlreadyExistsError
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import PlainPassword


class RegisterUserService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        password_hasher: PasswordHasher,
    ) -> None:
        self.unit_of_work_factory = unit_of_work_factory
        self.password_hasher = password_hasher

    async def execute(
        self,
        command: RegisterUserCommand,
    ) -> UserDTO:
        email = Email(command.email)
        password = PlainPassword(command.password)

        unit_of_work = self.unit_of_work_factory.create()

        async with unit_of_work:
            exists = await unit_of_work.users.exists_by_email(
                email.value,
            )

            if exists:
                raise UserAlreadyExistsError(
                    "A user with this email already exists",
                )

            password_hash = self.password_hasher.hash(
                password,
            )

            user = User.create(
                email=email,
                password_hash=password_hash,
            )

            await unit_of_work.users.add(user)

            return UserDTO(
                id=user.id,
                email=user.email.value,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
