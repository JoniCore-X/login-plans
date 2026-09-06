from abc import ABC, abstractmethod

from app.domain.plans.entities import Plan
from app.domain.plans.value_objects import PlanId
from app.domain.users.value_objects import UserId


class PlanRepository(ABC):
    @abstractmethod
    async def get_by_id(
        self,
        user_id: UserId,
        plan_id: PlanId,
    ) -> Plan | None:
        raise NotImplementedError

    @abstractmethod
    async def list_by_user(
        self,
        user_id: UserId,
    ) -> list[Plan]:
        raise NotImplementedError

    @abstractmethod
    async def add(
        self,
        plan: Plan,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update(
        self,
        plan: Plan,
    ) -> bool:
        """Persist changes; False means the stored version no longer matches."""
        raise NotImplementedError
