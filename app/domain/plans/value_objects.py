from dataclasses import dataclass
from uuid import UUID

from app.domain.plans.exceptions import (
    InvalidPlanDescriptionError,
    InvalidPlanNameError,
)

_MIN_NAME_LENGTH = 3
_MAX_NAME_LENGTH = 100
_MAX_DESCRIPTION_LENGTH = 1000


@dataclass(frozen=True, slots=True)
class PlanId:
    value: UUID

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True, slots=True)
class PlanName:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()

        if not (_MIN_NAME_LENGTH <= len(normalized) <= _MAX_NAME_LENGTH):
            raise InvalidPlanNameError(
                "Plan name must be between 3 and 100 characters.",
            )

        object.__setattr__(self, "value", normalized)


@dataclass(frozen=True, slots=True)
class PlanDescription:
    value: str | None

    def __post_init__(self) -> None:
        if self.value is not None and len(self.value) > _MAX_DESCRIPTION_LENGTH:
            raise InvalidPlanDescriptionError(
                "Plan description cannot exceed 1000 characters.",
            )
