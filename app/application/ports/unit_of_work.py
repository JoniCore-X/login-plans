from abc import ABC, abstractmethod

from app.application.plans.ports import PlanRepository
from app.application.sessions.ports import SessionRepository
from app.application.users.ports import UserRepository


class UnitOfWork(ABC):
    users: UserRepository
    sessions: SessionRepository
    plans: PlanRepository

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork": ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None: ...
