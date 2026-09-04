from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.password_hash import PasswordHash
from app.infrastructure.persistence.repositories.user import (
    PostgresUserRepository,
)


@pytest.mark.asyncio
async def test_user_repository_can_persist_user() -> None:
    settings = get_settings()

    engine = create_async_engine(
        settings.database_url.get_secret_value(),
    )

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        repository = PostgresUserRepository(session)

        user = User(
            id=uuid4(),
            email=Email(
                f"{uuid4()}@example.com",
            ),
            password_hash=PasswordHash(
                "test-hash",
            ),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        await repository.add(user)

        await session.commit()

        stored_user = await repository.get_by_id(
            user.id,
        )

        assert stored_user is not None
        assert stored_user.id == user.id
        assert stored_user.email.value == user.email.value

    await engine.dispose()
