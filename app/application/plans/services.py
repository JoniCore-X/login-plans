from uuid import uuid4

from app.application.plans.commands import (
    ChangePlanStatusCommand,
    CreatePlanCommand,
    PlanStatusAction,
    UpdatePlanCommand,
)
from app.application.plans.dto import PlanDTO
from app.application.plans.queries import (
    GetPlanByIdQuery,
    ListUserPlansQuery,
)
from app.application.ports.clock import Clock
from app.application.ports.unit_of_work_factory import UnitOfWorkFactory
from app.domain.plans.entities import Plan
from app.domain.plans.exceptions import (
    PlanNotFoundError,
    StalePlanError,
)
from app.domain.plans.value_objects import (
    PlanDescription,
    PlanId,
    PlanName,
)
from app.domain.users.value_objects import UserId


def plan_to_dto(plan: Plan) -> PlanDTO:
    return PlanDTO(
        id=plan.id.value,
        user_id=plan.user_id.value,
        name=plan.name.value,
        description=plan.description.value,
        status=plan.status.value,
        version=plan.version,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


class CreatePlanService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
    ) -> None:
        self.unit_of_work_factory = unit_of_work_factory
        self.clock = clock

    async def execute(
        self,
        command: CreatePlanCommand,
    ) -> PlanDTO:
        name = PlanName(command.name)
        description = PlanDescription(command.description)

        unit_of_work = self.unit_of_work_factory.create()

        async with unit_of_work:
            plan = Plan.create(
                plan_id=uuid4(),
                user_id=UserId(command.user_id),
                name=name,
                description=description,
                now=self.clock.now(),
            )

            await unit_of_work.plans.add(plan)

            return plan_to_dto(plan)


class UpdatePlanService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
    ) -> None:
        self.unit_of_work_factory = unit_of_work_factory
        self.clock = clock

    async def execute(
        self,
        command: UpdatePlanCommand,
    ) -> PlanDTO:
        name = PlanName(command.name) if command.name is not None else None
        description = (
            PlanDescription(command.description)
            if command.description is not None
            else None
        )

        unit_of_work = self.unit_of_work_factory.create()

        async with unit_of_work:
            plan = await unit_of_work.plans.get_by_id(
                UserId(command.user_id),
                PlanId(command.plan_id),
            )

            if plan is None:
                raise PlanNotFoundError(
                    "Plan not found.",
                )

            if plan.version != command.expected_version:
                raise StalePlanError(
                    "Plan was modified by another request.",
                )

            plan.update(
                name=name,
                description=description,
                now=self.clock.now(),
            )

            persisted = await unit_of_work.plans.update(plan)

            if not persisted:
                raise StalePlanError(
                    "Plan was modified by another request.",
                )

            return plan_to_dto(plan)


class ChangePlanStatusService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
        clock: Clock,
    ) -> None:
        self.unit_of_work_factory = unit_of_work_factory
        self.clock = clock

    async def execute(
        self,
        command: ChangePlanStatusCommand,
    ) -> PlanDTO:
        unit_of_work = self.unit_of_work_factory.create()

        async with unit_of_work:
            plan = await unit_of_work.plans.get_by_id(
                UserId(command.user_id),
                PlanId(command.plan_id),
            )

            if plan is None:
                raise PlanNotFoundError(
                    "Plan not found.",
                )

            if command.action == PlanStatusAction.PUBLISH:
                plan.publish(now=self.clock.now())
            else:
                plan.archive(now=self.clock.now())

            persisted = await unit_of_work.plans.update(plan)

            if not persisted:
                raise StalePlanError(
                    "Plan was modified by another request.",
                )

            return plan_to_dto(plan)


class GetPlanService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
    ) -> None:
        self.unit_of_work_factory = unit_of_work_factory

    async def execute(
        self,
        query: GetPlanByIdQuery,
    ) -> PlanDTO:
        unit_of_work = self.unit_of_work_factory.create()

        async with unit_of_work:
            plan = await unit_of_work.plans.get_by_id(
                UserId(query.user_id),
                PlanId(query.plan_id),
            )

            if plan is None:
                raise PlanNotFoundError(
                    "Plan not found.",
                )

            return plan_to_dto(plan)


class ListUserPlansService:
    def __init__(
        self,
        unit_of_work_factory: UnitOfWorkFactory,
    ) -> None:
        self.unit_of_work_factory = unit_of_work_factory

    async def execute(
        self,
        query: ListUserPlansQuery,
    ) -> list[PlanDTO]:
        unit_of_work = self.unit_of_work_factory.create()

        async with unit_of_work:
            plans = await unit_of_work.plans.list_by_user(
                UserId(query.user_id),
            )

            return [plan_to_dto(plan) for plan in plans]
