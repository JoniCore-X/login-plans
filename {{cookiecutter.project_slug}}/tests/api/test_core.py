import httpx
import pytest

from app.application.ports.health_checker import HealthChecker
from tests.factories import TestApplicationFactory


class FakeHealthyHealthChecker(HealthChecker):
    async def is_healthy(self) -> bool:
        return True


class FakeDeadHealthChecker(HealthChecker):
    async def is_healthy(self) -> bool:
        return False


@pytest.mark.asyncio
async def test_health_endpoint_returns_200_when_db_is_healthy(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "healthy"
    assert body["components"]["database"] == "connected"


@pytest.mark.asyncio
async def test_health_endpoint_returns_503_when_db_is_dead(
    test_application_factory: TestApplicationFactory,
) -> None:
    app = test_application_factory.create(
        health_checker=FakeDeadHealthChecker(),
    )

    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 503

    body = response.json()

    assert body["status"] == "unhealthy"
    assert body["components"]["database"] == "disconnected"


@pytest.mark.asyncio
async def test_root_endpoint(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/v1/")

    assert response.status_code == 200
    assert response.json()["application"] == "{{cookiecutter.project_name}}-test"
    assert response.json()["version"] == "v1"
