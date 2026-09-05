import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.database.engine import create_database_engine


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_connection() -> None:
    settings = get_settings()

    engine = create_database_engine(settings)

    async with engine.connect() as connection:
        result = await connection.execute(
            text("SELECT 1"),
        )

        assert result.scalar_one() == 1

    await engine.dispose()
