from abc import ABC, abstractmethod

from app.domain.users.entities import User
from app.domain.users.value_objects import Email, UserId


class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(
        self,
        user_id: UserId,
    ) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(
        self,
        email: Email,
    ) -> User | None:
        raise NotImplementedError

    @abstractmethod
    async def add(
        self,
        user: User,
    ) -> None:
        raise NotImplementedError
