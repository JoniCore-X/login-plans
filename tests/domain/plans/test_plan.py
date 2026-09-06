from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.domain.plans.entities import Plan
from app.domain.plans.enums import PlanStatus
from app.domain.plans.exceptions import (
    ImmutablePlanError,
    InvalidPlanDescriptionError,
    InvalidPlanNameError,
    InvalidPlanStateTransition,
)
from app.domain.plans.value_objects import (
    PlanDescription,
    PlanName,
)
from app.domain.users.value_objects import UserId
from tests.factories import plan_factory


def _owner() -> UserId:
    return UserId(UUID("00000000-0000-0000-0000-000000000001"))


def test_plan_is_created_draft() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)

    plan = Plan.create(
        plan_id=uuid4(),
        user_id=_owner(),
        name=PlanName("My plan"),
        description=PlanDescription("desc"),
        now=now,
    )

    assert plan.status == PlanStatus.DRAFT
    assert plan.version == 1
    assert plan.created_at == now


def test_update_draft_plan_increments_version() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)

    plan = plan_factory(status=PlanStatus.DRAFT, version=1)

    plan.update(
        name=PlanName("New name"),
        description=PlanDescription("new"),
        now=now,
    )

    assert plan.name.value == "New name"
    assert plan.version == 2
    assert plan.updated_at == now


def test_archived_plan_cannot_be_updated() -> None:
    plan = plan_factory(status=PlanStatus.ARCHIVED)

    with pytest.raises(ImmutablePlanError):
        plan.update(
            name=PlanName("New name"),
            now=datetime.now(UTC),
        )


def test_publish_transitions_draft_to_active() -> None:
    now = datetime.now(UTC)

    plan = plan_factory(status=PlanStatus.DRAFT, version=1)

    plan.publish(now=now)

    assert plan.status == PlanStatus.ACTIVE
    assert plan.version == 2


def test_publish_active_plan_is_rejected() -> None:
    plan = plan_factory(status=PlanStatus.ACTIVE)

    with pytest.raises(InvalidPlanStateTransition):
        plan.publish(now=datetime.now(UTC))


def test_archive_is_final_and_blocks_mutation() -> None:
    now = datetime.now(UTC)

    plan = plan_factory(status=PlanStatus.ACTIVE)

    plan.archive(now=now)

    assert plan.status == PlanStatus.ARCHIVED

    with pytest.raises(InvalidPlanStateTransition):
        plan.archive(now=now)

    with pytest.raises(ImmutablePlanError):
        plan.publish(now=now)


def test_plan_name_validation() -> None:
    with pytest.raises(InvalidPlanNameError):
        PlanName("ab")

    with pytest.raises(InvalidPlanNameError):
        PlanName("")

    with pytest.raises(InvalidPlanNameError):
        PlanName("x" * 101)

    assert PlanName("  My plan  ").value == "My plan"


def test_plan_description_validation() -> None:
    assert PlanDescription(None).value is None
    assert PlanDescription("ok").value == "ok"

    with pytest.raises(InvalidPlanDescriptionError):
        PlanDescription("x" * 1001)
