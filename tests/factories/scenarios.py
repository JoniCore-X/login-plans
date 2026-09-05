from dataclasses import dataclass

from app.application.commands.register_user import (
    RegisterUserCommand,
)
from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import PlainPassword
from tests.factories.commands import register_user_command_factory


@dataclass(frozen=True, slots=True)
class RegistrationScenario:
    email: Email
    password: PlainPassword
    command: RegisterUserCommand
    user: User | None = None


def registration_scenario_factory(
    *,
    email: str = "registration@example.com",
    password: str = "Strong-password-123!",
) -> RegistrationScenario:
    email_value = Email(email)
    password_value = PlainPassword(password)

    command = register_user_command_factory(
        email=email_value.value,
        password=password_value.value,
    )

    return RegistrationScenario(
        email=email_value,
        password=password_value,
        command=command,
    )
