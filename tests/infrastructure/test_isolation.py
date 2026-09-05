from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.password_hash import PasswordHash
from app.infrastructure.persistence.models.user import UserModel
from app.infrastructure.persistence.repositories.user import (
    PostgresUserRepository,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_data_is_visible_inside_test(
    test_session: AsyncSession,
) -> None:
    result = await test_session.execute(
        select(UserModel),
    )

    users = result.scalars().all()

    assert users == []


@pytest.mark.integration
@pytest.mark.asyncio
async def test_insert_is_rolled_back(
    test_session: AsyncSession,
) -> None:
    repository = PostgresUserRepository(
        test_session,
    )

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

    await test_session.flush()

    result = await test_session.execute(
        select(UserModel).where(
            UserModel.id == user.id,
        ),
    )

    stored_user = result.scalar_one_or_none()

    assert stored_user is not None
