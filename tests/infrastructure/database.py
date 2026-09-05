from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession


class TestDatabase:
    def __init__(
        self,
        engine: AsyncEngine,
    ) -> None:
        self.engine = engine
        self.connection: AsyncConnection | None = None
        self.session: AsyncSession | None = None

    async def start(self) -> AsyncSession:
        self.connection = await self.engine.connect()

        await self.connection.begin()

        self.session = AsyncSession(
            bind=self.connection,
            expire_on_commit=False,
        )

        return self.session

    async def stop(self) -> None:
        if self.session is not None:
            await self.session.close()

        if self.connection is not None:
            await self.connection.close()
