import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.persistence.models.audit_log import (
    AuditLogModel,
)
from app.infrastructure.persistence.models.plan import PlanModel
from tests.factories import TestApplicationFactory


async def register_verify_and_login(
    client: httpx.AsyncClient,
    factory: TestApplicationFactory,
    email: str,
    password: str = "Strong-password-123!",
) -> dict[str, str]:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )

    token = factory.email_sender.sent_verification_emails[-1][1]

    verify = await client.post(
        "/api/v1/auth/verify-email",
        json={"token": token},
    )
    assert verify.status_code == 204

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )

    assert login_response.status_code == 200

    return login_response.json()


def bearer(credential: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {credential}"}


@pytest.mark.asyncio
async def test_full_plan_lifecycle(
    client: httpx.AsyncClient,
    test_session: AsyncSession,
    test_application_factory: TestApplicationFactory,
) -> None:
    login = await register_verify_and_login(
        client, test_application_factory, "owner@example.com"
    )
    headers = bearer(login["credential"])

    # CREATE
    create = await client.post(
        "/api/v1/plans",
        json={"name": "My plan", "description": "desc"},
        headers=headers,
    )

    assert create.status_code == 201
    plan = create.json()
    assert plan["status"] == "draft"
    assert plan["version"] == 1
    assert plan["user_id"] == login["user_id"]

    # GET
    fetched = await client.get(
        f"/api/v1/plans/{plan['id']}",
        headers=headers,
    )
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "My plan"

    # UPDATE
    updated = await client.patch(
        f"/api/v1/plans/{plan['id']}",
        json={
            "name": "Renamed",
            "description": "new desc",
            "version": 1,
        },
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Renamed"
    assert updated.json()["version"] == 2

    # PUBLISH
    published = await client.post(
        f"/api/v1/plans/{plan['id']}/publish",
        headers=headers,
    )
    assert published.status_code == 200
    assert published.json()["status"] == "active"

    # ARCHIVE
    archived = await client.post(
        f"/api/v1/plans/{plan['id']}/archive",
        headers=headers,
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "archived"

    # DB state
    result = await test_session.execute(
        select(PlanModel).where(PlanModel.id == plan["id"]),
    )
    stored = result.scalar_one()
    assert stored.status == "archived"
    assert stored.version == 4

    # Audit trail: PlanCreated → PlanUpdated → PlanPublished → PlanArchived
    audit = await test_session.execute(
        select(AuditLogModel).order_by(AuditLogModel.occurred_at),
    )
    events = [row.event_type for row in audit.scalars().all()]

    plan_events = [e for e in events if e.startswith("Plan")]

    assert "UserRegistered" in events
    assert plan_events == [
        "PlanCreated",
        "PlanUpdated",
        "PlanPublished",
        "PlanArchived",
    ]


@pytest.mark.asyncio
async def test_create_plan_requires_authentication(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(
        "/api/v1/plans",
        json={"name": "My plan"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_plan_of_another_user_returns_404(
    client: httpx.AsyncClient,
    test_application_factory: TestApplicationFactory,
) -> None:
    owner = await register_verify_and_login(
        client, test_application_factory, "owner2@example.com"
    )
    intruder = await register_verify_and_login(
        client, test_application_factory, "intruder@example.com"
    )

    create = await client.post(
        "/api/v1/plans",
        json={"name": "Secret plan"},
        headers=bearer(owner["credential"]),
    )
    plan_id = create.json()["id"]

    response = await client.get(
        f"/api/v1/plans/{plan_id}",
        headers=bearer(intruder["credential"]),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_plan_with_stale_version_returns_409(
    client: httpx.AsyncClient,
    test_application_factory: TestApplicationFactory,
) -> None:
    login = await register_verify_and_login(
        client, test_application_factory, "stale@example.com"
    )
    headers = bearer(login["credential"])

    create = await client.post(
        "/api/v1/plans",
        json={"name": "Race plan"},
        headers=headers,
    )
    plan = create.json()

    # First update wins
    first = await client.patch(
        f"/api/v1/plans/{plan['id']}",
        json={"name": "First", "version": 1},
        headers=headers,
    )
    assert first.status_code == 200

    # Second update with stale version loses
    second = await client.patch(
        f"/api/v1/plans/{plan['id']}",
        json={"name": "Second", "version": 1},
        headers=headers,
    )
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_update_archived_plan_returns_400(
    client: httpx.AsyncClient,
    test_application_factory: TestApplicationFactory,
) -> None:
    login = await register_verify_and_login(
        client, test_application_factory, "archive@example.com"
    )
    headers = bearer(login["credential"])

    create = await client.post(
        "/api/v1/plans",
        json={"name": "Old plan"},
        headers=headers,
    )
    plan = create.json()

    await client.post(
        f"/api/v1/plans/{plan['id']}/archive",
        headers=headers,
    )

    response = await client.patch(
        f"/api/v1/plans/{plan['id']}",
        json={"name": "Nope", "version": 2},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "PLAN_IMMUTABLE"


@pytest.mark.asyncio
async def test_create_plan_with_invalid_name_returns_422(
    client: httpx.AsyncClient,
    test_application_factory: TestApplicationFactory,
) -> None:
    login = await register_verify_and_login(
        client, test_application_factory, "badname@example.com"
    )
    headers = bearer(login["credential"])

    response = await client.post(
        "/api/v1/plans",
        json={"name": "ab"},
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PLAN_NAME"


@pytest.mark.asyncio
async def test_list_plans_only_shows_own(
    client: httpx.AsyncClient,
    test_application_factory: TestApplicationFactory,
) -> None:
    owner = await register_verify_and_login(
        client, test_application_factory, "lister@example.com"
    )
    other = await register_verify_and_login(
        client, test_application_factory, "other@example.com"
    )

    await client.post(
        "/api/v1/plans",
        json={"name": "Mine"},
        headers=bearer(owner["credential"]),
    )
    await client.post(
        "/api/v1/plans",
        json={"name": "Theirs"},
        headers=bearer(other["credential"]),
    )

    response = await client.get(
        "/api/v1/plans",
        headers=bearer(owner["credential"]),
    )

    assert response.status_code == 200
    plans = response.json()
    assert len(plans) == 1
    assert plans[0]["name"] == "Mine"
