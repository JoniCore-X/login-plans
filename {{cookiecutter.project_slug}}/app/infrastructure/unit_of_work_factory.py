from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.ports.event_dispatcher import (
    EventDispatcher,
    NoOpEventDispatcher,
)
from app.application.ports.unit_of_work import UnitOfWork
from app.application.ports.unit_of_work_factory import UnitOfWorkFactory
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


class SqlAlchemyUnitOfWorkFactory(UnitOfWorkFactory):
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        event_dispatcher: EventDispatcher | None = None,
    ) -> None:
        self.session_factory = session_factory
        self.event_dispatcher = event_dispatcher or NoOpEventDispatcher()

    def create(self) -> UnitOfWork:
        session = self.session_factory()

        return SqlAlchemyUnitOfWork(
            session,
            self.event_dispatcher,
        )
