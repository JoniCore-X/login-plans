import httpx
import pytest

from tests.factories import TestApplicationFactory


@pytest.mark.asyncio
async def test_responses_include_security_headers(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/v1/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers["Permissions-Policy"]


@pytest.mark.asyncio
async def test_hsts_not_sent_in_development(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/v1/health")

    assert "Strict-Transport-Security" not in response.headers


@pytest.mark.asyncio
async def test_hsts_sent_in_production(
    test_application_factory: TestApplicationFactory,
) -> None:
    test_application_factory.settings = (
        test_application_factory.settings.model_copy(
            update={"app_env": "production"},
        )
    )
    app = test_application_factory.create()

    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/health")

    assert (
        response.headers["Strict-Transport-Security"]
        == "max-age=31536000; includeSubDomains"
    )


@pytest.mark.asyncio
async def test_cors_preflight_allowed_origin(
    client: httpx.AsyncClient,
) -> None:
    response = await client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert (
        response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    )


@pytest.mark.asyncio
async def test_cors_preflight_rejected_origin(
    client: httpx.AsyncClient,
) -> None:
    response = await client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.headers.get("access-control-allow-origin") is None
