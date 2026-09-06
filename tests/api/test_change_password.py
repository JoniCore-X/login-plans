import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.audit_log import (
    AuditLogModel,
)


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
async def test_change_password_revokes_other_sessions(
    client: httpx.AsyncClient,
    test_session: AsyncSession,
) -> None:
    # Device A (current session)
    login_a = await register_and_login(client, "change@example.com")

    # Device B (another active session for the same user)
    second_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "change@example.com",
            "password": "Strong-password-123!",
        },
    )
    credential_b = second_login.json()["credential"]

    # Change password from device A
    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "Strong-password-123!",
            "new_password": "NewStr0ng!Pass2026",
        },
        headers=bearer(login_a["credential"]),
    )

    assert response.status_code == 204

    # Current session still works
    me = await client.get(
        "/api/v1/auth/me",
        headers=bearer(login_a["credential"]),
    )
    assert me.status_code == 200

    # Device B session is purged
    me_b = await client.get(
        "/api/v1/auth/me",
        headers=bearer(credential_b),
    )
    assert me_b.status_code == 401

    # Old password rejected, new password accepted
    old_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "change@example.com",
            "password": "Strong-password-123!",
        },
    )
    assert old_login.status_code == 401

    new_login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "change@example.com",
            "password": "NewStr0ng!Pass2026",
        },
    )
    assert new_login.status_code == 200

    # Audit trail: PasswordChanged + SessionRevoked
    audit = await test_session.execute(
        select(AuditLogModel),
    )
    events = [row.event_type for row in audit.scalars().all()]

    assert "PasswordChanged" in events
    assert "SessionRevoked" in events


@pytest.mark.asyncio
async def test_change_password_with_wrong_current_returns_401(
    client: httpx.AsyncClient,
) -> None:
    login = await register_and_login(client, "wrong@example.com")

    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "Wrong-password-999",
            "new_password": "NewStr0ng!Pass2026",
        },
        headers=bearer(login["credential"]),
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_password_with_weak_new_password_returns_400(
    client: httpx.AsyncClient,
) -> None:
    login = await register_and_login(client, "weak@example.com")

    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "Strong-password-123!",
            "new_password": "weak",
        },
        headers=bearer(login["credential"]),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "WEAK_PASSWORD"


@pytest.mark.asyncio
async def test_change_password_without_authentication_returns_401(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "a",
            "new_password": "b",
        },
    )

    assert response.status_code == 401
