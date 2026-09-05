from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession

from app.domain.repositories.unit_of_work import UnitOfWork
from app.infrastructure.persistence.repositories.user import (
    PostgresUserRepository,
)


class TestDatabase:
    def __init__(
        self,
        engine: AsyncEngine,
    ) -> None:
        self.engine = engine
        self.connection: AsyncConnection | None = None
        self.transaction = None
        self.session: AsyncSession | None = None

    async def start(self) -> AsyncSession:
        self.connection = await self.engine.connect()

        self.transaction = await self.connection.begin()

        self.session = AsyncSession(
            bind=self.connection,
            expire_on_commit=False,
        )

        await self.session.begin_nested()

        sync_session = self.session.sync_session

        @event.listens_for(
            sync_session,
            "after_transaction_end",
        )
        def restart_savepoint(
            session,
            transaction,
        ) -> None:
            if transaction.nested and not transaction._parent.nested:
                session.begin_nested()

        return self.session

    async def stop(self) -> None:
        if self.session is not None:
            await self.session.close()

        if self.transaction is not None:
            if self.transaction.is_active:
                await self.transaction.rollback()

        if self.connection is not None:
            await self.connection.close()


class TestUnitOfWork(UnitOfWork):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session
        self.users = PostgresUserRepository(session)

    async def __aenter__(self) -> "TestUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        if exc_type is not None:
            await self.session.rollback()
            return

        await self.session.flush()


class TestUnitOfWorkFactory:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    def create(self) -> TestUnitOfWork:
        return TestUnitOfWork(
            self.session,
        )
