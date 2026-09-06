import httpx
import pytest

from tests.factories import TestApplicationFactory


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_prometheus_format(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/metrics")

    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text


@pytest.mark.asyncio
async def test_metrics_excluded_from_openapi(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/openapi.json")

    assert "/metrics" not in response.json()["paths"]


@pytest.mark.asyncio
async def test_health_endpoint_not_instrumented(
    client: httpx.AsyncClient,
) -> None:
    await client.get("/api/v1/health")

    metrics = await client.get("/metrics")

    assert "/api/v1/health" not in metrics.text


@pytest.mark.asyncio
async def test_login_success_increments_metric(
    client: httpx.AsyncClient,
    test_application_factory: TestApplicationFactory,
) -> None:
    from prometheus_client import REGISTRY

    before = (
        REGISTRY.get_sample_value(
            "auth_login_attempts_total",
            {"status": "success"},
        )
        or 0
    )

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "metrics@example.com",
            "password": "Strong-password-123!",
        },
    )

    await client.post(
        "/api/v1/auth/login",
        json={
            "email": "metrics@example.com",
            "password": "Strong-password-123!",
        },
    )

    after = (
        REGISTRY.get_sample_value(
            "auth_login_attempts_total",
            {"status": "success"},
        )
        or 0
    )

    assert after == before + 1


@pytest.mark.asyncio
async def test_login_failure_increments_metric(
    client: httpx.AsyncClient,
) -> None:
    from prometheus_client import REGISTRY

    before = (
        REGISTRY.get_sample_value(
            "auth_login_attempts_total",
            {"status": "failed_invalid_credentials"},
        )
        or 0
    )

    await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "Strong-password-123!",
        },
    )

    after = (
        REGISTRY.get_sample_value(
            "auth_login_attempts_total",
            {"status": "failed_invalid_credentials"},
        )
        or 0
    )

    assert after == before + 1


@pytest.mark.asyncio
async def test_plan_creation_increments_metric(
    client: httpx.AsyncClient,
    test_application_factory: TestApplicationFactory,
) -> None:
    from prometheus_client import REGISTRY

    before = REGISTRY.get_sample_value("plans_created_total") or 0

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "planmetrics@example.com",
            "password": "Strong-password-123!",
        },
    )

    token = test_application_factory.email_sender.sent_verification_emails[-1][1]
    await client.post(
        "/api/v1/auth/verify-email",
        json={"token": token},
    )

    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "planmetrics@example.com",
            "password": "Strong-password-123!",
        },
    )
    credential = login.json()["credential"]

    await client.post(
        "/api/v1/plans",
        json={"name": "Metrics plan"},
        headers={"Authorization": f"Bearer {credential}"},
    )

    after = REGISTRY.get_sample_value("plans_created_total") or 0

    assert after == before + 1


@pytest.mark.asyncio
async def test_audit_events_increments_metric(
    client: httpx.AsyncClient,
) -> None:
    from prometheus_client import REGISTRY

    before = (
        REGISTRY.get_sample_value(
            "audit_events_total",
            {"event_type": "UserRegistered"},
        )
        or 0
    )

    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "auditmetrics@example.com",
            "password": "Strong-password-123!",
        },
    )

    after = (
        REGISTRY.get_sample_value(
            "audit_events_total",
            {"event_type": "UserRegistered"},
        )
        or 0
    )

    assert after == before + 1
