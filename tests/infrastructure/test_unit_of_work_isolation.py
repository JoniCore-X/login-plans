import pytest

from app.application.ports.unit_of_work_factory import UnitOfWorkFactory
from app.domain.users.value_objects import Email
from tests.factories import user_factory


@pytest.mark.integration
@pytest.mark.asyncio
async def test_uow_insert_is_rolled_back(
    test_uow_factory: UnitOfWorkFactory,
) -> None:
    user = user_factory(
        email="uow-isolation@example.com",
    )

    async with test_uow_factory.create() as uow:
        await uow.users.add(user)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_uow_previous_test_data_does_not_exist(
    test_uow_factory: UnitOfWorkFactory,
) -> None:
    async with test_uow_factory.create() as uow:
        stored_user = await uow.users.get_by_email(
            Email("uow-isolation@example.com"),
        )

        assert stored_user is None
