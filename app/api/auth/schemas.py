from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RegisterRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    email: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    email: str
    status: str
    created_at: datetime
    updated_at: datetime
