import httpx
import pytest


@pytest.mark.integration
@pytest.mark.regression
@pytest.mark.asyncio
async def test_user_registration_remains_operational(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "regression@example.com",
            "password": "Strong-regression-password-123!",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["email"] == "regression@example.com"
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body

    assert "password" not in body
    assert "password_hash" not in body


@pytest.mark.integration
@pytest.mark.regression
@pytest.mark.asyncio
async def test_user_registration_preserves_email_normalization(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "  NORMALIZED@Example.COM  ",
            "password": "Strong-regression-password-123!",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "normalized@example.com"


@pytest.mark.integration
@pytest.mark.regression
@pytest.mark.asyncio
async def test_duplicate_registration_remains_rejected(
    client: httpx.AsyncClient,
) -> None:
    email = "regression-duplicate@example.com"

    first_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Strong-regression-password-123!",
        },
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "Another-regression-password-123!",
        },
    )

    assert second_response.status_code == 409
    assert second_response.json()["error"]["code"] == ("USER_ALREADY_EXISTS")
