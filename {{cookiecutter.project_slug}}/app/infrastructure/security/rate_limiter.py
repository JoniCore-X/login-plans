from collections import deque
from datetime import datetime, timedelta

from app.application.ports.clock import Clock
from app.application.ports.rate_limiter import RateLimiter


class InMemoryRateLimiter(RateLimiter):
    def __init__(
        self,
        clock: Clock,
        limit: int,
        window: timedelta,
    ) -> None:
        self.clock = clock
        self.limit = limit
        self.window = window
        self._attempts: dict[str, deque[datetime]] = {}

    async def allow(self, key: str) -> bool:
        now = self.clock.now()

        attempts = self._attempts.setdefault(key, deque())

        cutoff = now - self.window

        while attempts and attempts[0] <= cutoff:
            attempts.popleft()

        if len(attempts) >= self.limit:
            return False

        attempts.append(now)

        return True
