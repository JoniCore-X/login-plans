import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings


@pytest.mark.asyncio
async def test_database_connection() -> None:
    settings = get_settings()

    engine = create_async_engine(
        settings.database_url.get_secret_value(),
    )

    async with engine.connect() as connection:
        result = await connection.execute(
            text("SELECT 1"),
        )

        assert result.scalar_one() == 1

    await engine.dispose()
