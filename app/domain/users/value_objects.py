import re
from dataclasses import dataclass
from uuid import UUID

from app.domain.users.exceptions import UserDomainError


class InvalidEmailError(UserDomainError):
    """Raised when an email address is invalid."""


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
