import httpx
import pytest


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_user(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new-user@example.com",
            "password": "Strong-development-password-123!",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["email"] == "new-user@example.com"
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body

    assert "password" not in body
    assert "password_hash" not in body


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_same_email_again_is_allowed_in_new_test(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new-user@example.com",
            "password": "Strong-development-password-123!",
        },
    )

    assert response.status_code == 201
