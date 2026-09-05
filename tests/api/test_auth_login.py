import httpx
import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.session import SessionModel


async def register_user(
    client: httpx.AsyncClient,
    email: str,
    password: str,
) -> str:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


@pytest.mark.asyncio
async def test_login_successful(
    client: httpx.AsyncClient,
) -> None:
    user_id = await register_user(
        client,
        "login@example.com",
        "Strong-password-123!",
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "Strong-password-123!",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["user_id"] == user_id
    assert body["session_id"]
    assert body["expires_at"]
    assert "password" not in body
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_login_with_uppercase_email_is_normalized(
    client: httpx.AsyncClient,
) -> None:
    await register_user(
        client,
        "normalized@example.com",
        "Strong-password-123!",
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "  NORMALIZED@example.COM  ",
            "password": "Strong-password-123!",
        },
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_unknown_email_returns_generic_error(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nobody@example.com",
            "password": "whatever-123!",
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["error"]["code"] == "INVALID_CREDENTIALS"
    assert "exist" not in body["error"]["message"].lower()
    assert "password" not in body["error"]["message"].lower()


@pytest.mark.asyncio
async def test_login_wrong_password_returns_same_generic_error(
    client: httpx.AsyncClient,
) -> None:
    await register_user(
        client,
        "user@example.com",
        "Strong-password-123!",
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@example.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 401

    body = response.json()

    assert body["error"]["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_login_creates_session_in_database(
    client: httpx.AsyncClient,
    test_session: AsyncSession,
) -> None:
    user_id = await register_user(
        client,
        "session@example.com",
        "Strong-password-123!",
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "session@example.com",
            "password": "Strong-password-123!",
        },
    )

    assert response.status_code == 200

    session_id = response.json()["session_id"]

    result = await test_session.execute(
        select(SessionModel).where(
            SessionModel.id == session_id,
        ),
    )

    stored_session = result.scalar_one_or_none()

    assert stored_session is not None
    assert str(stored_session.user_id) == user_id
    assert stored_session.status == "active"


@pytest.mark.asyncio
async def test_logins_are_isolated_between_users(
    client: httpx.AsyncClient,
    test_session: AsyncSession,
) -> None:
    user_a_id = await register_user(
        client,
        "user-a@example.com",
        "Strong-password-123!",
    )
    user_b_id = await register_user(
        client,
        "user-b@example.com",
        "Strong-password-123!",
    )

    response_a = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "user-a@example.com",
            "password": "Strong-password-123!",
        },
    )
    response_b = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "user-b@example.com",
            "password": "Strong-password-123!",
        },
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    session_a_id = response_a.json()["session_id"]
    session_b_id = response_b.json()["session_id"]

    assert session_a_id != session_b_id

    result = await test_session.execute(
        select(SessionModel).where(
            SessionModel.id.in_(
                [session_a_id, session_b_id],
            ),
        ),
    )

    sessions = {str(row.id): str(row.user_id) for row in result.scalars().all()}

    assert sessions[session_a_id] == user_a_id
    assert sessions[session_b_id] == user_b_id


@pytest.mark.asyncio
async def test_login_suspended_user_returns_forbidden(
    client: httpx.AsyncClient,
    test_session: AsyncSession,
) -> None:
    user_id = await register_user(
        client,
        "suspended@example.com",
        "Strong-password-123!",
    )

    await test_session.execute(
        text("UPDATE users SET status = 'suspended' WHERE id = :user_id"),
        {"user_id": user_id},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "suspended@example.com",
            "password": "Strong-password-123!",
        },
    )

    assert response.status_code == 403

    body = response.json()

    assert body["error"]["code"] == "AUTHENTICATION_NOT_ALLOWED"


@pytest.mark.asyncio
async def test_login_expires_in_future(
    client: httpx.AsyncClient,
) -> None:
    await register_user(
        client,
        "expiry@example.com",
        "Strong-password-123!",
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "expiry@example.com",
            "password": "Strong-password-123!",
        },
    )

    assert response.status_code == 200

    from datetime import UTC, datetime

    expires_at = datetime.fromisoformat(
        response.json()["expires_at"],
    )

    assert expires_at > datetime.now(UTC)


@pytest.mark.asyncio
async def test_login_never_exposes_password(
    client: httpx.AsyncClient,
) -> None:
    await register_user(
        client,
        "leak@example.com",
        "Strong-password-123!",
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "leak@example.com",
            "password": "Strong-password-123!",
        },
    )

    body = response.json()

    assert "password" not in body
    assert "password_hash" not in body
    assert "token" not in body
