from app.application.plans.ports import PlanRepository
from app.domain.plans.entities import Plan
from app.domain.plans.value_objects import PlanId
from app.domain.users.value_objects import UserId


class FakePlanRepository(PlanRepository):
    def __init__(self) -> None:
        self.plans: list[Plan] = []

    async def get_by_id(
        self,
        user_id: UserId,
        plan_id: PlanId,
    ) -> Plan | None:
        for plan in self.plans:
            if plan.id == plan_id and plan.user_id == user_id:
                return plan

        return None

    async def list_by_user(
        self,
        user_id: UserId,
    ) -> list[Plan]:
        return [plan for plan in self.plans if plan.user_id == user_id]

    async def add(self, plan: Plan) -> None:
        self.plans.append(plan)

    async def update(self, plan: Plan) -> bool:
        for index, existing in enumerate(self.plans):
            if existing.id == plan.id:
                self.plans[index] = plan
                return True

        return False
