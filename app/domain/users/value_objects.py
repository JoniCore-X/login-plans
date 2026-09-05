import re
from dataclasses import dataclass
from uuid import UUID

from app.domain.users.exceptions import UserDomainError


class InvalidEmailError(UserDomainError):
    """Raised when an email address is invalid."""


class WeakPasswordError(UserDomainError):
    """Raised when a plaintext password violates the password policy."""


_EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
)


@dataclass(frozen=True, slots=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()

        if not _EMAIL_PATTERN.match(normalized):
            raise InvalidEmailError("Invalid email address.")

        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


_COMMON_PASSWORDS = frozenset(
    {
        "password",
        "123456",
        "12345678",
        "123456789",
        "1234567890",
        "123456789012",
        "qwerty",
        "abc123",
        "monkey",
        "1234567",
        "letmein",
        "trustno1",
        "dragon",
        "baseball",
        "iloveyou",
        "master",
        "sunshine",
        "ashley",
        "bailey",
        "passw0rd",
        "shadow",
        "123123",
        "654321",
        "superman",
        "qazwsx",
        "michael",
        "football",
        "password1",
        "password123",
        "batman",
        "login",
        "admin",
        "welcome",
        "hello",
        "charlie",
        "donald",
        "qwerty123",
        "1q2w3e4r",
        "111111",
        "000000",
    }
)

_MIN_PASSWORD_LENGTH = 12


@dataclass(frozen=True, slots=True)
class PlainPassword:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("Password must be a string.")

        if not self.value or not self.value.strip():
            raise WeakPasswordError(
                "Password cannot be empty or whitespace.",
            )

        if len(self.value) < _MIN_PASSWORD_LENGTH:
            raise WeakPasswordError(
                "Password must be at least 12 characters.",
            )

        if self.value.lower() in _COMMON_PASSWORDS:
            raise WeakPasswordError(
                "Password is too common and was rejected.",
            )

        if self.value.isdigit() or self.value.isalpha():
            raise WeakPasswordError(
                "Password must mix letters, digits or symbols.",
            )


@dataclass(frozen=True, slots=True)
class PasswordHash:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Password hash cannot be empty.")


@dataclass(frozen=True, slots=True)
class UserId:
    value: UUID

    def __str__(self) -> str:
        return str(self.value)
