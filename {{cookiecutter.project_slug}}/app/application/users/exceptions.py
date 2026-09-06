class UserApplicationError(Exception):
    """Base exception for user application errors."""


class InvalidCredentialsError(UserApplicationError):
    """Raised when authentication credentials are invalid."""


class UserCannotAuthenticateError(UserApplicationError):
    """Raised when the user's state prevents authentication."""
