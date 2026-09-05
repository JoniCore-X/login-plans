import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.ports.health_checker import HealthChecker

logger = logging.getLogger(__name__)


class PostgresHealthChecker(HealthChecker):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def is_healthy(self) -> bool:
        try:
            async with self._session_factory() as session:
                await session.execute(text("SELECT 1"))

            return True
        except Exception:
            logger.exception("Database health check failed")

            return False
