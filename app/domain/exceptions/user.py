from app.domain.exceptions.base import DomainError


class UserAlreadyExistsError(DomainError):
    """Raised when a user already exists."""


class UserNotFoundError(DomainError):
    """Raised when a user cannot be found."""


class InvalidEmailError(DomainError):
    """Raised when an email is invalid."""
