from collections.abc import Awaitable
from datetime import timedelta
from typing import cast
from uuid import uuid4

import redis.asyncio as redis

from app.application.ports.clock import Clock
from app.application.ports.rate_limiter import RateLimiter
from app.infrastructure.tracing import trace_span

_ALLOW_SCRIPT = """
local key = KEYS[1]
local cutoff = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local member = ARGV[4]
local ttl_ms = tonumber(ARGV[5])

redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)
local count = redis.call('ZCARD', key)

if count < limit then
    redis.call('ZADD', key, now, member)
    redis.call('PEXPIRE', key, ttl_ms)
    return 1
end

return 0
"""


class RedisRateLimiter(RateLimiter):
    def __init__(
        self,
        redis_client: redis.Redis,
        clock: Clock,
        limit: int,
        window: timedelta,
    ) -> None:
        self._redis = redis_client
        self.clock = clock
        self.limit = limit
        self.window = window

    @trace_span("redis.rate_limit_check")
    async def allow(self, key: str) -> bool:
        now_ms = int(self.clock.now().timestamp() * 1000)
        window_ms = int(self.window.total_seconds() * 1000)
        cutoff_ms = now_ms - window_ms

        member = f"{now_ms}:{uuid4().hex}"

        allowed = await cast(
            Awaitable[int],
            self._redis.eval(
                _ALLOW_SCRIPT,
                1,
                f"rate-limit:{key}",
                cutoff_ms,
                self.limit,
                now_ms,
                member,
                window_ms,
            ),
        )

        return bool(allowed)
