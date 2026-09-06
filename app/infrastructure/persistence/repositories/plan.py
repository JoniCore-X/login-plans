from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.plans.ports import PlanRepository
from app.domain.plans.entities import Plan
from app.domain.plans.value_objects import PlanId
from app.domain.users.value_objects import UserId
from app.infrastructure.persistence.mappers.plan import (
    plan_to_domain,
    plan_to_model,
)
from app.infrastructure.persistence.models.plan import PlanModel


class PostgresPlanRepository(PlanRepository):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(
        self,
        user_id: UserId,
        plan_id: PlanId,
    ) -> Plan | None:
        result = await self.session.execute(
            select(PlanModel).where(
                PlanModel.id == plan_id.value,
                PlanModel.user_id == user_id.value,
            ),
        )

        model = result.scalar_one_or_none()

        if model is None:
            return None

        return plan_to_domain(model)

    async def list_by_user(
        self,
        user_id: UserId,
    ) -> list[Plan]:
        result = await self.session.execute(
            select(PlanModel)
            .where(PlanModel.user_id == user_id.value)
            .order_by(PlanModel.created_at.desc()),
        )

        return [plan_to_domain(model) for model in result.scalars().all()]

    async def add(
        self,
        plan: Plan,
    ) -> None:
        self.session.add(
            plan_to_model(plan),
        )

    async def update(
        self,
        plan: Plan,
    ) -> bool:
        expected_version = plan.version - 1

        result = await self.session.execute(
            update(PlanModel)
            .where(
                PlanModel.id == plan.id.value,
                PlanModel.user_id == plan.user_id.value,
                PlanModel.version == expected_version,
            )
            .values(
                name=plan.name.value,
                description=plan.description.value,
                status=plan.status.value,
                version=plan.version,
                updated_at=plan.updated_at,
            ),
        )

        rowcount = getattr(result, "rowcount", 0)

        return bool(rowcount and rowcount > 0)
