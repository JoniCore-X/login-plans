from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.plans.entities import Plan
from app.domain.plans.enums import PlanStatus
from app.domain.plans.value_objects import (
    PlanDescription,
    PlanId,
    PlanName,
)
from app.domain.users.value_objects import UserId


def plan_factory(
    *,
    plan_id: UUID | None = None,
    user_id: UUID | None = None,
    name: str = "My plan",
    description: str | None = "A test plan",
    status: PlanStatus = PlanStatus.DRAFT,
    version: int = 1,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> Plan:
    now = datetime.now(UTC)

    return Plan(
        id=PlanId(plan_id or uuid4()),
        user_id=UserId(user_id or uuid4()),
        name=PlanName(name),
        description=PlanDescription(description),
        status=status,
        version=version,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )
