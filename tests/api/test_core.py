import httpx
import pytest


@pytest.mark.asyncio
async def test_health_endpoint(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }


@pytest.mark.asyncio
async def test_root_endpoint(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/v1/")

    assert response.status_code == 200
    assert response.json()["application"] == "login-plans-test"
    assert response.json()["version"] == "v1"
