from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    email: str
    password: str
