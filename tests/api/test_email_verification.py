import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.audit_log import (
    AuditLogModel,
)
from tests.factories import TestApplicationFactory


def bearer(credential: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {credential}"}


@pytest.mark.asyncio
async def test_register_sends_verification_email_and_unverified_cannot_create_plan(
    client: httpx.AsyncClient,
    test_application_factory: TestApplicationFactory,
) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "ghost@example.com",
            "password": "Strong-password-123!",
        },
    )

    # Token was "sent" via the fake sender
    sender = test_application_factory.email_sender
    assert len(sender.sent_verification_emails) == 1
    to, token = sender.sent_verification_emails[-1]
    assert to == "ghost@example.com"
    assert token

    # Unverified user can log in...
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "ghost@example.com",
            "password": "Strong-password-123!",
        },
    )
    assert login.status_code == 200
    credential = login.json()["credential"]

    # ...but cannot create plans (the lock)
    create = await client.post(
        "/api/v1/plans",
        json={"name": "Ghost plan"},
        headers=bearer(credential),
    )
    assert create.status_code == 403
    assert create.json()["error"]["code"] == "EMAIL_NOT_VERIFIED"


@pytest.mark.asyncio
async def test_verify_email_unlocks_plan_creation(
    client: httpx.AsyncClient,
    test_application_factory: TestApplicationFactory,
    test_session: AsyncSession,
) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "human@example.com",
            "password": "Strong-password-123!",
        },
    )

    sender = test_application_factory.email_sender
    _, token = sender.sent_verification_emails[-1]

    verify = await client.post(
        "/api/v1/auth/verify-email",
        json={"token": token},
    )
    assert verify.status_code == 204

    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "human@example.com",
            "password": "Strong-password-123!",
        },
    )
    credential = login.json()["credential"]

    create = await client.post(
        "/api/v1/plans",
        json={"name": "Real plan"},
        headers=bearer(credential),
    )
    assert create.status_code == 201

    # Audit trail records the verification
    audit = await test_session.execute(
        select(AuditLogModel),
    )
    events = [row.event_type for row in audit.scalars().all()]
    assert "EmailVerified" in events


@pytest.mark.asyncio
async def test_verify_email_with_invalid_token_returns_400(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/auth/verify-email",
        json={"token": "not-a-real-token"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_VERIFICATION_TOKEN"


@pytest.mark.asyncio
async def test_verify_email_with_used_token_returns_400(
    client: httpx.AsyncClient,
    test_application_factory: TestApplicationFactory,
) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "twice@example.com",
            "password": "Strong-password-123!",
        },
    )

    sender = test_application_factory.email_sender
    _, token = sender.sent_verification_emails[-1]

    first = await client.post(
        "/api/v1/auth/verify-email",
        json={"token": token},
    )
    assert first.status_code == 204

    second = await client.post(
        "/api/v1/auth/verify-email",
        json={"token": token},
    )
    assert second.status_code == 400
