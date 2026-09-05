from uuid import uuid4

import httpx
import pytest

from app.main import app


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_rejects_invalid_email() -> None:
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "password": "Development-password-123!",
            },
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_EMAIL"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_rejects_duplicate_email() -> None:
    email = f"duplicate-{uuid4()}@example.com"
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        first_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "Development-password-123!",
            },
        )

        assert first_response.status_code == 201

        second_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "Another-password-123!",
            },
        )

        assert second_response.status_code == 409
        assert second_response.json()["error"]["code"] == "USER_ALREADY_EXISTS"
