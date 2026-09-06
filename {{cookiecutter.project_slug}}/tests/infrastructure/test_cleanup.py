import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.user import UserModel


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_starts_clean(
    test_session: AsyncSession,
) -> None:
    result = await test_session.execute(
        select(UserModel),
    )

    users = result.scalars().all()

    assert users == []
