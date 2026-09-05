from app.domain.exceptions.base import DomainError


class SessionDomainError(DomainError):
    """Base exception for session domain errors."""


class InvalidSessionStateTransition(SessionDomainError):
    """Raised when an invalid session state transition is requested."""
