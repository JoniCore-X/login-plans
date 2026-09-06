from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.plans.enums import PlanStatus
from app.domain.plans.exceptions import (
    ImmutablePlanError,
    InvalidPlanStateTransition,
)
from app.domain.plans.value_objects import (
    PlanDescription,
    PlanId,
    PlanName,
)
from app.domain.users.value_objects import UserId


@dataclass(slots=True)
class Plan:
    id: PlanId
    user_id: UserId
    name: PlanName
    description: PlanDescription
    status: PlanStatus
    version: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        plan_id: UUID,
        user_id: UserId,
        name: PlanName,
        description: PlanDescription,
        now: datetime,
    ) -> "Plan":
        return cls(
            id=PlanId(plan_id),
            user_id=user_id,
            name=name,
            description=description,
            status=PlanStatus.DRAFT,
            version=1,
            created_at=now,
            updated_at=now,
        )

    def update(
        self,
        *,
        name: PlanName | None = None,
        description: PlanDescription | None = None,
        now: datetime,
    ) -> None:
        if self.status == PlanStatus.ARCHIVED:
            raise ImmutablePlanError(
                "Archived plans cannot be modified.",
            )

        if name is not None:
            self.name = name

        if description is not None:
            self.description = description

        self.version += 1
        self.updated_at = now

    def publish(self, *, now: datetime) -> None:
        if self.status == PlanStatus.ARCHIVED:
            raise ImmutablePlanError(
                "Archived plans cannot be published.",
            )

        if self.status != PlanStatus.DRAFT:
            raise InvalidPlanStateTransition(
                "Only draft plans can be published.",
            )

        self.status = PlanStatus.ACTIVE
        self.version += 1
        self.updated_at = now

    def archive(self, *, now: datetime) -> None:
        if self.status == PlanStatus.ARCHIVED:
            raise InvalidPlanStateTransition(
                "Plan is already archived.",
            )

        self.status = PlanStatus.ARCHIVED
        self.version += 1
        self.updated_at = now
