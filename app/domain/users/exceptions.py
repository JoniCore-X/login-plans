from app.domain.exceptions.base import DomainError


class UserDomainError(DomainError):
    """Base exception for user domain errors."""


class InvalidUserStateTransition(UserDomainError):
    """Raised when an invalid user state transition is requested."""


class InactiveUserError(UserDomainError):
    """Raised when an inactive user performs a forbidden operation."""


class SuspendedUserError(UserDomainError):
    """Raised when a suspended user performs a forbidden operation."""


class UserAlreadyExistsError(UserDomainError):
    """Raised when a user already exists."""


class UserNotFoundError(UserDomainError):
    """Raised when a user cannot be found."""
