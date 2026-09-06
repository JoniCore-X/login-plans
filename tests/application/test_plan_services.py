import pytest

from app.application.plans.commands import (
    ChangePlanStatusCommand,
    CreatePlanCommand,
    PlanStatusAction,
    UpdatePlanCommand,
)
from app.application.plans.queries import (
    GetPlanByIdQuery,
    ListUserPlansQuery,
)
from app.application.plans.services import (
    ChangePlanStatusService,
    CreatePlanService,
    GetPlanService,
    ListUserPlansService,
    UpdatePlanService,
)
from app.domain.plans.enums import PlanStatus
from app.domain.plans.exceptions import (
    ImmutablePlanError,
    PlanNotFoundError,
    StalePlanError,
)
from tests.factories import FixedClock, plan_factory, user_factory
from tests.fakes.plans import FakePlanRepository


class FakeClockUoW:
    pass


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.plans = FakePlanRepository()
        self.events: list = []
        self.committed = False

    def collect_event(self, event: object) -> None:
        self.events.append(event)

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(self, *args: object) -> None:
        self.committed = True


class FakeUnitOfWorkFactory:
    def __init__(self) -> None:
        self.unit_of_work = FakeUnitOfWork()

    def create(self) -> FakeUnitOfWork:
        return self.unit_of_work


@pytest.mark.asyncio
async def test_create_plan_assigns_owner() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    service = CreatePlanService(
        unit_of_work_factory=uow_factory,  # type: ignore[arg-type]
        clock=FixedClock(),
    )

    user = user_factory()

    result = await service.execute(
        CreatePlanCommand(
            user_id=user.id.value,
            name="My plan",
            description="desc",
        ),
    )

    assert result.user_id == user.id.value
    assert result.status == "draft"
    assert result.version == 1


@pytest.mark.asyncio
async def test_get_plan_by_other_user_raises_not_found() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    service = GetPlanService(
        unit_of_work_factory=uow_factory,  # type: ignore[arg-type]
    )

    owner = user_factory()
    intruder = user_factory()
    plan = plan_factory(user_id=owner.id.value)
    uow_factory.unit_of_work.plans.plans.append(plan)

    with pytest.raises(PlanNotFoundError):
        await service.execute(
            GetPlanByIdQuery(
                user_id=intruder.id.value,
                plan_id=plan.id.value,
            ),
        )


@pytest.mark.asyncio
async def test_update_plan_with_wrong_user_raises_not_found() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    service = UpdatePlanService(
        unit_of_work_factory=uow_factory,  # type: ignore[arg-type]
        clock=FixedClock(),
    )

    owner = user_factory()
    intruder = user_factory()
    plan = plan_factory(user_id=owner.id.value)
    uow_factory.unit_of_work.plans.plans.append(plan)

    with pytest.raises(PlanNotFoundError):
        await service.execute(
            UpdatePlanCommand(
                user_id=intruder.id.value,
                plan_id=plan.id.value,
                expected_version=plan.version,
                name="New name",
                description=None,
            ),
        )


@pytest.mark.asyncio
async def test_update_with_stale_version_raises_conflict() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    service = UpdatePlanService(
        unit_of_work_factory=uow_factory,  # type: ignore[arg-type]
        clock=FixedClock(),
    )

    owner = user_factory()
    plan = plan_factory(
        user_id=owner.id.value,
        version=2,
    )
    uow_factory.unit_of_work.plans.plans.append(plan)

    with pytest.raises(StalePlanError):
        await service.execute(
            UpdatePlanCommand(
                user_id=owner.id.value,
                plan_id=plan.id.value,
                expected_version=1,
                name="New name",
                description=None,
            ),
        )


@pytest.mark.asyncio
async def test_update_archived_plan_raises_immutable() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    service = UpdatePlanService(
        unit_of_work_factory=uow_factory,  # type: ignore[arg-type]
        clock=FixedClock(),
    )

    owner = user_factory()
    plan = plan_factory(
        user_id=owner.id.value,
        status=PlanStatus.ARCHIVED,
    )
    uow_factory.unit_of_work.plans.plans.append(plan)

    with pytest.raises(ImmutablePlanError):
        await service.execute(
            UpdatePlanCommand(
                user_id=owner.id.value,
                plan_id=plan.id.value,
                expected_version=plan.version,
                name="New name",
                description=None,
            ),
        )


@pytest.mark.asyncio
async def test_publish_plan() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    service = ChangePlanStatusService(
        unit_of_work_factory=uow_factory,  # type: ignore[arg-type]
        clock=FixedClock(),
    )

    owner = user_factory()
    plan = plan_factory(user_id=owner.id.value)
    uow_factory.unit_of_work.plans.plans.append(plan)

    result = await service.execute(
        ChangePlanStatusCommand(
            user_id=owner.id.value,
            plan_id=plan.id.value,
            action=PlanStatusAction.PUBLISH,
        ),
    )

    assert result.status == "active"
    assert result.version == 2


@pytest.mark.asyncio
async def test_list_plans_only_returns_own() -> None:
    uow_factory = FakeUnitOfWorkFactory()
    service = ListUserPlansService(
        unit_of_work_factory=uow_factory,  # type: ignore[arg-type]
    )

    owner = user_factory()
    other = user_factory()
    uow_factory.unit_of_work.plans.plans.append(
        plan_factory(user_id=owner.id.value, name="Mine")
    )
    uow_factory.unit_of_work.plans.plans.append(
        plan_factory(user_id=other.id.value, name="Theirs")
    )

    results = await service.execute(
        ListUserPlansQuery(user_id=owner.id.value),
    )

    assert len(results) == 1
    assert results[0].name == "Mine"
