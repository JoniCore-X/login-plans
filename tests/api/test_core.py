from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }


def test_root_endpoint() -> None:
    response = client.get("/api/v1/")

    assert response.status_code == 200
    assert response.json()["application"] == "login-plans-test"
    assert response.json()["version"] == "v1"
