from app.application.users.commands import (
    RegisterUserCommand,
)


def register_user_command_factory(
    *,
    email: str = "user@example.com",
    password: str = "Strong-password-123!",
) -> RegisterUserCommand:
    return RegisterUserCommand(
        email=email,
        password=password,
    )
