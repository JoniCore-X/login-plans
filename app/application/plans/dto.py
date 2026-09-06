from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PlanDTO:
    id: UUID
    user_id: UUID
    name: str
    description: str | None
    status: str
    version: int
    created_at: datetime
    updated_at: datetime
