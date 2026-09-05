from abc import ABC, abstractmethod

from app.application.users.ports import UserRepository


class UnitOfWork(ABC):
    users: UserRepository

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork": ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None: ...
