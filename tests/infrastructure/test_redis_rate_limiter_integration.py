import os
from datetime import timedelta

import pytest
import pytest_asyncio
import redis.asyncio as redis

from app.infrastructure.security.redis_rate_limiter import (
    RedisRateLimiter,
)
from tests.factories import FixedClock

REDIS_URL = os.environ.get(
    "REDIS_URL",
    "redis://localhost:6379/0",
)


async def _redis_reachable() -> bool:
    try:
        client = redis.Redis.from_url(REDIS_URL)
        await client.ping()
        await client.aclose()
        return True
    except Exception:
        return False


@pytest_asyncio.fixture
async def redis_client() -> redis.Redis:
    if not await _redis_reachable():
        pytest.skip("Redis is not available")

    client = redis.Redis.from_url(
        REDIS_URL,
        decode_responses=True,
    )

    yield client

    await client.flushdb()
    await client.aclose()


@pytest.mark.asyncio
async def test_two_instances_share_counter(
    redis_client: redis.Redis,
) -> None:
    # Dos "instancias" de la app compartiendo el mismo Redis
    limiter_a = RedisRateLimiter(
        redis_client=redis_client,
        clock=FixedClock(),  # type: ignore[arg-type]
        limit=3,
        window=timedelta(minutes=5),
    )
    limiter_b = RedisRateLimiter(
        redis_client=redis_client,
        clock=FixedClock(),  # type: ignore[arg-type]
        limit=3,
        window=timedelta(minutes=5),
    )

    key = "login:1.2.3.4"

    assert await limiter_a.allow(key) is True
    assert await limiter_b.allow(key) is True
    assert await limiter_a.allow(key) is True

    # La cuarta petición es bloqueada sin importar la instancia
    assert await limiter_b.allow(key) is False


@pytest.mark.asyncio
async def test_window_expiration_frees_slots(
    redis_client: redis.Redis,
) -> None:
    clock = FixedClock()
    limiter = RedisRateLimiter(
        redis_client=redis_client,
        clock=clock,
        limit=2,
        window=timedelta(minutes=5),
    )

    key = "login:expiry"

    assert await limiter.allow(key) is True
    assert await limiter.allow(key) is True
    assert await limiter.allow(key) is False

    # Avanzar el reloj más allá de la ventana libera los slots
    clock.advance(timedelta(minutes=6))

    assert await limiter.allow(key) is True
