class UserDomainError(Exception):
    """Base exception for user domain errors."""


class InvalidUserStateTransition(UserDomainError):
    """Raised when an invalid user state transition is requested."""


class InactiveUserError(UserDomainError):
    """Raised when an inactive user performs a forbidden operation."""


class SuspendedUserError(UserDomainError):
    """Raised when a suspended user performs a forbidden operation."""
