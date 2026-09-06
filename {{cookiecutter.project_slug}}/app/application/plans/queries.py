from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class GetPlanByIdQuery:
    user_id: UUID
    plan_id: UUID


@dataclass(frozen=True, slots=True)
class ListUserPlansQuery:
    user_id: UUID
