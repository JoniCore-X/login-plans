class AuthenticationError(Exception):
    """Authentication failed."""


class RateLimitExceededError(Exception):
    """Too many requests within the allowed window."""
