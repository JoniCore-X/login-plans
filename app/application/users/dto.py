from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.users.enums import UserStatus


@dataclass(frozen=True, slots=True)
class UserDTO:
    id: UUID
    email: str
    status: UserStatus
    created_at: datetime
    updated_at: datetime
