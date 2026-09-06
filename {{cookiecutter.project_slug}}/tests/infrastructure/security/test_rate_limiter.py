from datetime import timedelta

import pytest

from app.infrastructure.security.rate_limiter import (
    InMemoryRateLimiter,
)
from tests.factories import FixedClock


@pytest.mark.asyncio
async def test_allows_requests_up_to_limit() -> None:
    limiter = InMemoryRateLimiter(
        clock=FixedClock(),
        limit=3,
        window=timedelta(minutes=5),
    )

    assert await limiter.allow("ip:1") is True
    assert await limiter.allow("ip:1") is True
    assert await limiter.allow("ip:1") is True


@pytest.mark.asyncio
async def test_blocks_after_limit() -> None:
    limiter = InMemoryRateLimiter(
        clock=FixedClock(),
        limit=3,
        window=timedelta(minutes=5),
    )

    for _ in range(3):
        await limiter.allow("ip:1")

    assert await limiter.allow("ip:1") is False


@pytest.mark.asyncio
async def test_different_keys_are_independent() -> None:
    limiter = InMemoryRateLimiter(
        clock=FixedClock(),
        limit=2,
        window=timedelta(minutes=5),
    )

    await limiter.allow("ip:a")
    await limiter.allow("ip:a")

    assert await limiter.allow("ip:b") is True


@pytest.mark.asyncio
async def test_window_expiry_allows_again() -> None:
    clock = FixedClock()

    limiter = InMemoryRateLimiter(
        clock=clock,
        limit=1,
        window=timedelta(minutes=5),
    )

    assert await limiter.allow("ip:1") is True
    assert await limiter.allow("ip:1") is False

    clock.current = clock.current + timedelta(minutes=6)

    assert await limiter.allow("ip:1") is True
