import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.audit_log import (
    AuditLogModel,
)
from tests.factories import TestApplicationFactory


@pytest.mark.asyncio
async def test_audit_log_carries_request_id(
    client: httpx.AsyncClient,
    test_application_factory: TestApplicationFactory,
    test_session: AsyncSession,
) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "trace@example.com",
            "password": "Strong-password-123!",
        },
    )

    token = test_application_factory.email_sender.sent_verification_emails[-1][1]

    await client.post(
        "/api/v1/auth/verify-email",
        json={"token": token},
    )

    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "trace@example.com",
            "password": "Strong-password-123!",
        },
    )
    credential = login.json()["credential"]

    # El request_id externo fluye: response → audit_logs
    response = await client.post(
        "/api/v1/plans",
        json={"name": "Traced plan"},
        headers={
            "Authorization": f"Bearer {credential}",
            "X-Request-ID": "trace-correlation-abc",
        },
    )
    assert response.status_code == 201

    audit = await test_session.execute(
        select(AuditLogModel).where(
            AuditLogModel.request_id == "trace-correlation-abc"
        ),
    )
    rows = audit.scalars().all()

    assert rows
    assert "PlanCreated" in [row.event_type for row in rows]
