from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.event_dispatcher import EventDispatcher
from app.application.ports.unit_of_work import UnitOfWork
from app.domain.events import DomainEvent
from app.infrastructure.persistence.repositories.plan import (
    PostgresPlanRepository,
)
from app.infrastructure.persistence.repositories.session import (
    PostgresSessionRepository,
)
from app.infrastructure.persistence.repositories.user import (
    PostgresUserRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(
        self,
        session: AsyncSession,
        event_dispatcher: EventDispatcher,
    ) -> None:
        self.session = session
        self.users = PostgresUserRepository(session)
        self.sessions = PostgresSessionRepository(session)
        self.plans = PostgresPlanRepository(session)
        self._events: list[DomainEvent] = []
        self._event_dispatcher = event_dispatcher

    def collect_event(
        self,
        event: DomainEvent,
    ) -> None:
        self._events.append(event)

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object,
    ) -> None:
        try:
            if exc_type is None:
                await self.session.commit()

                await self._event_dispatcher.dispatch(
                    self._events,
                )
            else:
                await self.session.rollback()
        finally:
            self._events = []
            await self.session.close()
