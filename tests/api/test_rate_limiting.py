from datetime import timedelta

import httpx
import pytest

from app.infrastructure.clock import SystemClock
from app.infrastructure.security.rate_limiter import (
    InMemoryRateLimiter,
)
from tests.factories import TestApplicationFactory


@pytest.mark.asyncio
async def test_login_rate_limit_blocks_after_limit(
    test_application_factory: TestApplicationFactory,
) -> None:
    rate_limiter = InMemoryRateLimiter(
        clock=SystemClock(),
        limit=3,
        window=timedelta(minutes=5),
    )

    app = test_application_factory.create(
        rate_limiter=rate_limiter,
    )

    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "limited@example.com",
                "password": "Strong-password-123!",
            },
        )

        for _ in range(3):
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "limited@example.com",
                    "password": "wrong-password-1",
                },
            )

            assert response.status_code == 401

        blocked = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "limited@example.com",
                "password": "wrong-password-1",
            },
        )

        assert blocked.status_code == 429

        body = blocked.json()

        assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"
