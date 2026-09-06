from abc import ABC, abstractmethod

from app.domain.events import DomainEvent


class EventDispatcher(ABC):
    @abstractmethod
    async def dispatch(
        self,
        events: list[DomainEvent],
    ) -> None:
        raise NotImplementedError


class NoOpEventDispatcher(EventDispatcher):
    async def dispatch(
        self,
        events: list[DomainEvent],
    ) -> None:
        pass
