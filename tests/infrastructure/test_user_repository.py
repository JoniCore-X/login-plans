import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.users.exceptions import UserAlreadyExistsError
from app.infrastructure.persistence.repositories.user import (
    PostgresUserRepository,
)
from tests.factories import user_factory


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_repository_can_persist_user(
    test_session: AsyncSession,
) -> None:
    repository = PostgresUserRepository(
        test_session,
    )

    user = user_factory()

    await repository.add(user)

    await test_session.flush()

    stored_user = await repository.get_by_id(
        user.id,
    )

    assert stored_user is not None
    assert stored_user.id == user.id
    assert stored_user.email.value == user.email.value


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_repository_rejects_duplicate_email(
    test_session: AsyncSession,
) -> None:
    repository = PostgresUserRepository(
        test_session,
    )

    first = user_factory(
        email="duplicate@example.com",
    )
    second = user_factory(
        email="duplicate@example.com",
    )

    await repository.add(first)

    with pytest.raises(UserAlreadyExistsError):
        await repository.add(second)

    await test_session.rollback()
