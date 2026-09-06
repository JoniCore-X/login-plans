from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CreatePlanCommand:
    user_id: UUID
    name: str
    description: str | None


@dataclass(frozen=True, slots=True)
class UpdatePlanCommand:
    user_id: UUID
    plan_id: UUID
    expected_version: int
    name: str | None
    description: str | None


class PlanStatusAction(StrEnum):
    PUBLISH = "publish"
    ARCHIVE = "archive"


@dataclass(frozen=True, slots=True)
class ChangePlanStatusCommand:
    user_id: UUID
    plan_id: UUID
    action: PlanStatusAction
