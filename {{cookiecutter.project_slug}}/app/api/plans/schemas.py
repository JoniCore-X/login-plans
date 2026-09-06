from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreatePlanRequest(BaseModel):
    name: str
    description: str | None = None


class UpdatePlanRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    version: int


class PlanResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    user_id: UUID
    name: str
    description: str | None
    status: str
    version: int
    created_at: datetime
    updated_at: datetime
