from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.unit_of_work import UnitOfWork
from app.infrastructure.persistence.repositories.session import (
    PostgresSessionRepository,
)
from app.infrastructure.persistence.repositories.user import (
    PostgresUserRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = PostgresUserRepository(session)
        self.sessions = PostgresSessionRepository(session)

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None:
        try:
            if exc_type is not None:
                await self.session.rollback()
                return

            await self.session.commit()
        finally:
            await self.session.close()
