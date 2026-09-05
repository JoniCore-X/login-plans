from datetime import datetime
from uuid import UUID, uuid4

from app.domain.entities.user import User
from tests.factories.values import (
    email_factory,
    password_hash_factory,
)


def user_factory(
    *,
    user_id: UUID | None = None,
    email: str | None = None,
    password_hash: str = "test-password-hash",
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
) -> User:
    now = datetime.now()

    return User(
        id=user_id or uuid4(),
        email=email_factory(email),
        password_hash=password_hash_factory(
            password_hash,
        ),
        created_at=created_at or now,
        updated_at=updated_at or now,
    )
