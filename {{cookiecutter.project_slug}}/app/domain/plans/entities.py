from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from app.domain.events import (
    DomainEvent,
    PlanArchived,
    PlanCreated,
    PlanPublished,
    PlanUpdated,
)
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
    _events: list[DomainEvent] = field(
        default_factory=list,
        repr=False,
    )

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
        plan = cls(
            id=PlanId(plan_id),
            user_id=user_id,
            name=name,
            description=description,
            status=PlanStatus.DRAFT,
            version=1,
            created_at=now,
            updated_at=now,
        )

        plan.register_event(
            PlanCreated(
                occurred_at=now,
                plan_id=plan_id,
                user_id=user_id.value,
                name=name.value,
            ),
        )

        return plan

    def register_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        events = self._events
        self._events = []
        return events

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

        self.register_event(
            PlanUpdated(
                occurred_at=now,
                plan_id=self.id.value,
                user_id=self.user_id.value,
            ),
        )

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

        self.register_event(
            PlanPublished(
                occurred_at=now,
                plan_id=self.id.value,
                user_id=self.user_id.value,
            ),
        )

    def archive(self, *, now: datetime) -> None:
        if self.status == PlanStatus.ARCHIVED:
            raise InvalidPlanStateTransition(
                "Plan is already archived.",
            )

        self.status = PlanStatus.ARCHIVED
        self.version += 1
        self.updated_at = now

        self.register_event(
            PlanArchived(
                occurred_at=now,
                plan_id=self.id.value,
                user_id=self.user_id.value,
            ),
        )
