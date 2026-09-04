from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class UserDTO:
    id: UUID
    email: str
    created_at: datetime
    updated_at: datetime
