import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.plans.enums import PlanStatus
from app.domain.plans.value_objects import PlanId
from app.domain.users.value_objects import UserId
from app.infrastructure.persistence.repositories.plan import (
    PostgresPlanRepository,
)
from app.infrastructure.persistence.repositories.user import (
    PostgresUserRepository,
)
from tests.factories import plan_factory, user_factory


@pytest.mark.integration
@pytest.mark.asyncio
async def test_plan_repository_persists_and_reads(
    test_session: AsyncSession,
) -> None:
    user_repository = PostgresUserRepository(test_session)
    plan_repository = PostgresPlanRepository(test_session)

    user = user_factory()
    await user_repository.add(user)
    await test_session.flush()

    plan = plan_factory(user_id=user.id.value)

    await plan_repository.add(plan)
    await test_session.flush()

    found = await plan_repository.get_by_id(
        UserId(user.id.value),
        PlanId(plan.id.value),
    )

    assert found is not None
    assert found.id == plan.id
    assert found.status == PlanStatus.DRAFT
    assert found.version == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_plan_repository_ownership_filter(
    test_session: AsyncSession,
) -> None:
    user_repository = PostgresUserRepository(test_session)
    plan_repository = PostgresPlanRepository(test_session)

    owner = user_factory()
    intruder = user_factory()
    await user_repository.add(owner)
    await user_repository.add(intruder)
    await test_session.flush()

    plan = plan_factory(user_id=owner.id.value)

    await plan_repository.add(plan)
    await test_session.flush()

    found = await plan_repository.get_by_id(
        UserId(intruder.id.value),
        PlanId(plan.id.value),
    )

    assert found is None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_plan_repository_optimistic_locking(
    test_session: AsyncSession,
) -> None:
    user_repository = PostgresUserRepository(test_session)
    plan_repository = PostgresPlanRepository(test_session)

    user = user_factory()
    await user_repository.add(user)
    await test_session.flush()

    plan = plan_factory(user_id=user.id.value, version=1)
    await plan_repository.add(plan)
    await test_session.flush()

    # First writer succeeds
    plan.version = 2
    first = await plan_repository.update(plan)
    assert first is True

    # Second writer with stale expected_version fails
    stale = plan_factory(
        plan_id=plan.id.value,
        user_id=user.id.value,
        version=1,
    )
    stale.version = 2
    second = await plan_repository.update(stale)

    assert second is False
