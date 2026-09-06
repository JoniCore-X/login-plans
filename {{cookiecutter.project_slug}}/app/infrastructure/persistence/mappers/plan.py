from app.domain.plans.entities import Plan
from app.domain.plans.enums import PlanStatus
from app.domain.plans.value_objects import (
    PlanDescription,
    PlanId,
    PlanName,
)
from app.domain.users.value_objects import UserId
from app.infrastructure.persistence.models.plan import PlanModel


def plan_to_model(plan: Plan) -> PlanModel:
    return PlanModel(
        id=plan.id.value,
        user_id=plan.user_id.value,
        name=plan.name.value,
        description=plan.description.value,
        status=plan.status.value,
        version=plan.version,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def plan_to_domain(model: PlanModel) -> Plan:
    return Plan(
        id=PlanId(model.id),
        user_id=UserId(model.user_id),
        name=PlanName(model.name),
        description=PlanDescription(model.description),
        status=PlanStatus(model.status),
        version=model.version,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
