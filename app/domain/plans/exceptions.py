from app.domain.exceptions.base import DomainError


class PlanDomainError(DomainError):
    """Base exception for plan domain errors."""


class PlanNotFoundError(PlanDomainError):
    """Raised when a plan cannot be found."""


class ImmutablePlanError(PlanDomainError):
    """Raised when an archived plan is modified."""


class OwnershipViolationError(PlanDomainError):
    """Raised when a user accesses a plan they do not own."""


class StalePlanError(PlanDomainError):
    """Raised when a plan was modified by a concurrent request."""


class InvalidPlanStateTransition(PlanDomainError):
    """Raised when an invalid plan state transition is requested."""


class InvalidPlanNameError(PlanDomainError):
    """Raised when a plan name is invalid."""


class InvalidPlanDescriptionError(PlanDomainError):
    """Raised when a plan description is invalid."""
