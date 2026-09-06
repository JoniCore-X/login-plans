from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.bootstrap.container import ApplicationContainer
from app.core.config import Settings
from app.infrastructure.security.rate_limiter import (
    InMemoryRateLimiter,
)
from app.infrastructure.security.redis_rate_limiter import (
    RedisRateLimiter,
)


class FakeRedisClient:
    def __init__(self, result: int) -> None:
        self.result = result
        self.calls: list[tuple] = []

    async def eval(self, *args: object) -> int:
        self.calls.append(args)
        return self.result


class FakeClock:
    def now(self) -> datetime:
        return datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


@pytest.mark.asyncio
async def test_allow_returns_true_when_under_limit() -> None:
    fake_redis = FakeRedisClient(result=1)
    limiter = RedisRateLimiter(
        redis_client=fake_redis,  # type: ignore[arg-type]
        clock=FakeClock(),  # type: ignore[arg-type]
        limit=10,
        window=timedelta(minutes=5),
    )

    assert await limiter.allow("login:1.2.3.4") is True


@pytest.mark.asyncio
async def test_allow_returns_false_when_at_limit() -> None:
    fake_redis = FakeRedisClient(result=0)
    limiter = RedisRateLimiter(
        redis_client=fake_redis,  # type: ignore[arg-type]
        clock=FakeClock(),  # type: ignore[arg-type]
        limit=10,
        window=timedelta(minutes=5),
    )

    assert await limiter.allow("login:1.2.3.4") is False


@pytest.mark.asyncio
async def test_allow_invokes_atomic_sliding_window_script() -> None:
    fake_redis = FakeRedisClient(result=1)
    limiter = RedisRateLimiter(
        redis_client=fake_redis,  # type: ignore[arg-type]
        clock=FakeClock(),  # type: ignore[arg-type]
        limit=10,
        window=timedelta(minutes=5),
    )

    await limiter.allow("login:1.2.3.4")

    (
        script,
        num_keys,
        key,
        cutoff,
        limit,
        now,
        member,
        ttl,
    ) = fake_redis.calls[0]

    assert "ZREMRANGEBYSCORE" in script
    assert "ZCARD" in script
    assert "ZADD" in script
    assert "PEXPIRE" in script
    assert num_keys == 1
    assert key == "rate-limit:login:1.2.3.4"
    assert limit == 10
    assert now == cutoff + 300_000
    assert ttl == 300_000
    assert str(member).startswith(str(now))


def _settings(redis_url: str | None = None) -> Settings:
    return Settings(
        app_env="test",
        database_url="postgresql+asyncpg://x:x@localhost:5432/x",  # type: ignore[arg-type]
        redis_url=redis_url,
    )


@pytest.mark.asyncio
async def test_container_uses_in_memory_without_redis_url() -> None:
    container = ApplicationContainer(
        settings=_settings(redis_url=None),
        password_hasher=MagicMock(),
        unit_of_work_factory=MagicMock(),
    )

    assert isinstance(container.rate_limiter, InMemoryRateLimiter)


@pytest.mark.asyncio
async def test_container_uses_redis_with_redis_url() -> None:
    container = ApplicationContainer(
        settings=_settings(redis_url="redis://localhost:6379/0"),
        password_hasher=MagicMock(),
        unit_of_work_factory=MagicMock(),
    )

    assert isinstance(container.rate_limiter, RedisRateLimiter)
