from abc import ABC, abstractmethod


class RateLimiter(ABC):
    @abstractmethod
    async def allow(self, key: str) -> bool:
        raise NotImplementedError
