from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
@pytest.mark.asyncio
async def test_data_is_rolled_back_after_test(
    test_session: AsyncSession,
) -> None:
    await test_session.execute(
        text(
            """
            INSERT INTO users (
                id,
                email,
                password_hash,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :email,
                :password_hash,
                NOW(),
                NOW()
            )
            """
        ),
        {
            "id": str(uuid4()),
            "email": "isolation@example.com",
            "password_hash": "test-hash",
        },
    )

    await test_session.flush()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_previous_test_data_does_not_exist(
    test_session: AsyncSession,
) -> None:
    result = await test_session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM users
            WHERE email = 'isolation@example.com'
            """
        )
    )

    assert result.scalar_one() == 0
