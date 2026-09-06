from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RegisterRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    email: str
    password: str


class LoginRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    email: str
    password: str


class VerifyEmailRequest(BaseModel):
    token: str


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    current_password: str
    new_password: str


class LoginResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    user_id: UUID
    session_id: UUID
    credential: str
    expires_at: datetime


class MeResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    user_id: UUID
    session_id: UUID


class UserResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    email: str
    status: str
    created_at: datetime
    updated_at: datetime
