import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.session import SessionModel


async def register_and_login(
    client: httpx.AsyncClient,
    email: str,
    password: str = "Strong-password-123!",
) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )

    assert login_response.status_code == 200

    return login_response.json()


def bearer(credential: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {credential}"}


@pytest.mark.asyncio
async def test_logout_returns_204(
    client: httpx.AsyncClient,
) -> None:
    login = await register_and_login(
        client,
        "logout@example.com",
    )

    response = await client.post(
        "/api/v1/auth/logout",
        headers=bearer(login["credential"]),
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_logout_invalidates_session(
    client: httpx.AsyncClient,
    test_session: AsyncSession,
) -> None:
    login = await register_and_login(
        client,
        "logout2@example.com",
    )

    await client.post(
        "/api/v1/auth/logout",
        headers=bearer(login["credential"]),
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers=bearer(login["credential"]),
    )

    assert response.status_code == 401

    result = await test_session.execute(
        select(SessionModel).where(
            SessionModel.id == login["session_id"],
        ),
    )

    stored = result.scalar_one()

    assert stored.status == "revoked"
    assert stored.revoked_at is not None


@pytest.mark.asyncio
async def test_logout_twice_returns_401(
    client: httpx.AsyncClient,
) -> None:
    login = await register_and_login(
        client,
        "logout3@example.com",
    )

    first = await client.post(
        "/api/v1/auth/logout",
        headers=bearer(login["credential"]),
    )

    assert first.status_code == 204

    second = await client.post(
        "/api/v1/auth/logout",
        headers=bearer(login["credential"]),
    )

    assert second.status_code == 401


@pytest.mark.asyncio
async def test_logout_with_invalid_credential_returns_401(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/logout",
        headers=bearer("not-a-real-credential"),
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_without_authorization_returns_401(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 401
