from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from app.domain.value_objects.email import Email
from app.domain.value_objects.password_hash import PasswordHash


@dataclass
class User:
    id: UUID
    email: Email
    password_hash: PasswordHash
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        email: Email,
        password_hash: PasswordHash,
    ) -> "User":
        now = datetime.now()

        return cls(
            id=uuid4(),
            email=email,
            password_hash=password_hash,
            created_at=now,
            updated_at=now,
        )
