import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.user import UserModel
from app.infrastructure.persistence.repositories.user import (
    PostgresUserRepository,
)
from tests.factories import user_factory


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

    user = user_factory()

    await repository.add(user)

    await test_session.flush()

    result = await test_session.execute(
        select(UserModel).where(
            UserModel.id == user.id.value,
        ),
    )

    stored_user = result.scalar_one_or_none()

    assert stored_user is not None
