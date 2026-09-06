from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from app.core.config import Settings
from app.database.engine import (
    create_database_engine,
    create_session_factory,
)


class Database:
    def __init__(self, settings: Settings) -> None:
        self.engine: AsyncEngine = create_database_engine(settings)

        self.session_factory: async_sessionmaker[AsyncSession] = create_session_factory(
            self.engine
        )

    async def dispose(self) -> None:
        await self.engine.dispose()
