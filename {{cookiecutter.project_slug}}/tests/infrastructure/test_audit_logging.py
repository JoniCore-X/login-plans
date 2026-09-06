from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import (
    PlanCreated,
    ReplayAttackDetected,
)
from app.infrastructure.events.audit_log_dispatcher import (
    AuditLogDispatcher,
)
from app.infrastructure.persistence.models.audit_log import (
    AuditLogModel,
)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_audit_log_dispatcher_persists_event(
    test_session: AsyncSession,
    test_session_factory,
) -> None:
    dispatcher = AuditLogDispatcher(test_session_factory)

    plan_id = uuid4()
    user_id = uuid4()

    await dispatcher.dispatch(
        [
            PlanCreated(
                occurred_at=datetime.now(UTC),
                plan_id=plan_id,
                user_id=user_id,
                name="My plan",
            ),
        ],
    )

    result = await test_session.execute(
        select(AuditLogModel),
    )
    rows = result.scalars().all()

    assert len(rows) == 1

    row = rows[0]
    assert row.event_type == "PlanCreated"
    assert row.user_id == user_id
    assert row.payload["plan_id"] == str(plan_id)
    assert row.payload["name"] == "My plan"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_audit_log_dispatcher_serializes_uuids(
    test_session: AsyncSession,
    test_session_factory,
) -> None:
    dispatcher = AuditLogDispatcher(test_session_factory)

    await dispatcher.dispatch(
        [
            ReplayAttackDetected(
                occurred_at=datetime.now(UTC),
                session_id=uuid4(),
                family_id=uuid4(),
                user_id=uuid4(),
            ),
        ],
    )

    result = await test_session.execute(
        select(AuditLogModel),
    )
    row = result.scalars().one()

    assert row.event_type == "ReplayAttackDetected"
    assert isinstance(row.payload["session_id"], str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_audit_log_dispatcher_ignores_empty(
    test_session_factory,
) -> None:
    dispatcher = AuditLogDispatcher(test_session_factory)

    await dispatcher.dispatch([])
