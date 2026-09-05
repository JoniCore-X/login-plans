from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.domain.users.entities import User
from app.domain.users.enums import UserStatus
from app.domain.users.value_objects import (
    Email,
    PasswordHash,
    UserId,
)


def user_factory(
    *,
    user_id: UUID | None = None,
    email: str | None = None,
    password_hash: str = "test-password-hash",
    status: UserStatus = UserStatus.ACTIVE,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> User:
    now = datetime.now(UTC)

    return User(
        id=UserId(user_id or uuid4()),
        email=Email(email or f"{uuid4()}@example.com"),
        password_hash=PasswordHash(password_hash),
        status=status,
        created_at=created_at or now,
        updated_at=updated_at or now,
    )
