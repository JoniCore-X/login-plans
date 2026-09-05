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
async def test_rotate_returns_new_credential(
    client: httpx.AsyncClient,
) -> None:
    login = await register_and_login(
        client,
        "rotate@example.com",
    )

    response = await client.post(
        "/api/v1/auth/rotate",
        headers=bearer(login["credential"]),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["user_id"] == login["user_id"]
    assert body["session_id"] != login["session_id"]
    assert body["credential"] != login["credential"]
    assert body["expires_at"] == login["expires_at"]


@pytest.mark.asyncio
async def test_old_credential_stops_working_after_rotation(
    client: httpx.AsyncClient,
) -> None:
    login = await register_and_login(
        client,
        "rotate2@example.com",
    )

    await client.post(
        "/api/v1/auth/rotate",
        headers=bearer(login["credential"]),
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers=bearer(login["credential"]),
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_new_credential_works_after_rotation(
    client: httpx.AsyncClient,
) -> None:
    login = await register_and_login(
        client,
        "rotate3@example.com",
    )

    rotate_response = await client.post(
        "/api/v1/auth/rotate",
        headers=bearer(login["credential"]),
    )

    new_credential = rotate_response.json()["credential"]

    response = await client.get(
        "/api/v1/auth/me",
        headers=bearer(new_credential),
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == login["user_id"]


@pytest.mark.asyncio
async def test_replay_of_old_credential_revokes_entire_family(
    client: httpx.AsyncClient,
    test_session: AsyncSession,
) -> None:
    login = await register_and_login(
        client,
        "rotate4@example.com",
    )

    rotate_response = await client.post(
        "/api/v1/auth/rotate",
        headers=bearer(login["credential"]),
    )

    new_credential = rotate_response.json()["credential"]

    replay = await client.post(
        "/api/v1/auth/rotate",
        headers=bearer(login["credential"]),
    )

    assert replay.status_code == 401

    result = await test_session.execute(
        select(SessionModel).where(
            SessionModel.user_id == login["user_id"],
        ),
    )

    sessions = result.scalars().all()

    assert all(session.status == "revoked" for session in sessions)

    me_response = await client.get(
        "/api/v1/auth/me",
        headers=bearer(new_credential),
    )

    assert me_response.status_code == 401


@pytest.mark.asyncio
async def test_rotate_with_invalid_credential_returns_401(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/rotate",
        headers=bearer("not-a-real-credential"),
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_rotate_without_authorization_returns_401(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post("/api/v1/auth/rotate")

    assert response.status_code == 401
