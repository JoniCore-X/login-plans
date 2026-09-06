import httpx
import pytest
from fastapi import FastAPI

from tests.factories import TestApplicationFactory


@pytest.fixture
def leaky_app(
    test_application_factory: TestApplicationFactory,
) -> FastAPI:
    application = test_application_factory.create()

    @application.get("/api/v1/test/boom")
    def boom() -> None:
        raise RuntimeError(
            "FATAL: DB_PASSWORD='super_secret_prod_pass' leaked!",
        )

    return application


@pytest.mark.asyncio
async def test_unhandled_exception_returns_generic_500(
    leaky_app: FastAPI,
) -> None:
    transport = httpx.ASGITransport(
        app=leaky_app,
        raise_app_exceptions=False,
    )

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/test/boom")

    assert response.status_code == 500

    body = response.json()

    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["error"]["message"] == (
        "Internal server error. Please try again later."
    )

    assert "DB_PASSWORD" not in response.text
    assert "super_secret_prod_pass" not in response.text
    assert "Traceback" not in response.text
    assert "RuntimeError" not in response.text


@pytest.mark.asyncio
async def test_weak_password_error_is_visible_to_client(
    leaky_app: FastAPI,
) -> None:
    transport = httpx.ASGITransport(app=leaky_app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weak@example.com",
                "password": "123",
            },
        )

    assert response.status_code == 400

    body = response.json()

    assert body["error"]["code"] == "WEAK_PASSWORD"
    assert "12 characters" in body["error"]["message"]


@pytest.mark.asyncio
async def test_domain_error_does_not_leak_internals(
    leaky_app: FastAPI,
) -> None:
    transport = httpx.ASGITransport(app=leaky_app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "a@example.com",
                "password": "a-strong-password-1",
            },
        )
        assert response.status_code == 201

        duplicate = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "a@example.com",
                "password": "a-strong-password-1",
            },
        )

    assert duplicate.status_code == 409
    assert "email" not in duplicate.json()["error"]["message"].lower()
    assert "already" not in duplicate.json()["error"]["message"].lower()
