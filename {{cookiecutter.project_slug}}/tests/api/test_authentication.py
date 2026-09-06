from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.session import SessionModel


async def register_and_login(
    client: httpx.AsyncClient,
    email: str,
    password: str = "Strong-password-123!",
) -> dict[str, str]:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )

    assert register_response.status_code == 201

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )

    assert login_response.status_code == 200

    return login_response.json()


def bearer(credential: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {credential}"}


@pytest.mark.asyncio
async def test_me_without_authorization_header_returns_401(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_basic_auth_returns_401(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Basic abc123"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_empty_bearer_returns_401(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_fake_credential_returns_401(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/auth/me",
        headers=bearer("not-a-real-credential"),
    )

    assert response.status_code == 401

    body = response.json()

    assert body["error"]["code"] == "AUTHENTICATION_FAILED"


@pytest.mark.asyncio
async def test_me_with_valid_credential_returns_200(
    client: httpx.AsyncClient,
) -> None:
    login = await register_and_login(
        client,
        "me@example.com",
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers=bearer(login["credential"]),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["user_id"] == login["user_id"]
    assert body["session_id"] == login["session_id"]


@pytest.mark.asyncio
async def test_me_with_revoked_session_returns_401(
    client: httpx.AsyncClient,
    test_session: AsyncSession,
) -> None:
    login = await register_and_login(
        client,
        "revoked@example.com",
    )

    await test_session.execute(
        update(SessionModel)
        .where(SessionModel.id == login["session_id"])
        .values(
            status="revoked",
            revoked_at=datetime.now(UTC),
        ),
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers=bearer(login["credential"]),
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_expired_session_returns_401(
    client: httpx.AsyncClient,
    test_session: AsyncSession,
) -> None:
    login = await register_and_login(
        client,
        "expired@example.com",
    )

    await test_session.execute(
        update(SessionModel)
        .where(SessionModel.id == login["session_id"])
        .values(
            expires_at=datetime.now(UTC) - timedelta(hours=1),
        ),
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers=bearer(login["credential"]),
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_credentials_are_isolated_between_users(
    client: httpx.AsyncClient,
) -> None:
    login_a = await register_and_login(
        client,
        "user-a@example.com",
    )
    login_b = await register_and_login(
        client,
        "user-b@example.com",
    )

    response_a = await client.get(
        "/api/v1/auth/me",
        headers=bearer(login_a["credential"]),
    )
    response_b = await client.get(
        "/api/v1/auth/me",
        headers=bearer(login_b["credential"]),
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200
    assert response_a.json()["user_id"] == login_a["user_id"]
    assert response_b.json()["user_id"] == login_b["user_id"]
    assert response_a.json()["user_id"] != response_b.json()["user_id"]


@pytest.mark.asyncio
async def test_tampered_credential_returns_401(
    client: httpx.AsyncClient,
) -> None:
    login = await register_and_login(
        client,
        "tampered@example.com",
    )

    credential = login["credential"]
    tampered = credential[:-1] + ("a" if credential[-1] != "a" else "b")

    response = await client.get(
        "/api/v1/auth/me",
        headers=bearer(tampered),
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_does_not_expose_sensitive_fields(
    client: httpx.AsyncClient,
) -> None:
    login = await register_and_login(
        client,
        "fields@example.com",
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers=bearer(login["credential"]),
    )

    body = response.json()

    assert "credential" not in body
    assert "credential_hash" not in body
    assert "password" not in body
    assert "password_hash" not in body
