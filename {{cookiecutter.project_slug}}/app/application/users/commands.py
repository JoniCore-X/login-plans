from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class ChangePasswordCommand:
    user_id: UUID
    session_id: UUID
    current_password: str
    new_password: str


@dataclass(frozen=True, slots=True)
class VerifyEmailCommand:
    token: str


@dataclass(frozen=True, slots=True)
class LoginUserCommand:
    email: str
    password: str
