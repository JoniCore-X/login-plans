from abc import ABC, abstractmethod


class HealthChecker(ABC):
    @abstractmethod
    async def is_healthy(self) -> bool:
        """Whether the critical component is reachable and operative."""
        raise NotImplementedError
