from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.auth.dependencies import get_current_user_id
from app.api.dependencies import (
    get_change_plan_status_service,
    get_create_plan_service,
    get_get_plan_service,
    get_list_user_plans_service,
    get_update_plan_service,
)
from app.api.plans.schemas import (
    CreatePlanRequest,
    PlanResponse,
    UpdatePlanRequest,
)
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
from app.application.plans.services import (
    ChangePlanStatusService,
    CreatePlanService,
    GetPlanService,
    ListUserPlansService,
    UpdatePlanService,
)
from app.domain.users.value_objects import UserId

router = APIRouter(
    prefix="/plans",
    tags=["plans"],
)


def _to_response(plan: PlanDTO) -> PlanResponse:
    return PlanResponse(
        id=plan.id,
        user_id=plan.user_id,
        name=plan.name,
        description=plan.description,
        status=plan.status,
        version=plan.version,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


@router.post(
    "",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_plan(
    request: CreatePlanRequest,
    user_id: Annotated[UserId, Depends(get_current_user_id)],
    service: Annotated[
        CreatePlanService,
        Depends(get_create_plan_service),
    ],
) -> PlanResponse:
    result = await service.execute(
        CreatePlanCommand(
            user_id=user_id.value,
            name=request.name,
            description=request.description,
        ),
    )

    return _to_response(result)


@router.get(
    "",
    response_model=list[PlanResponse],
    status_code=status.HTTP_200_OK,
)
async def list_plans(
    user_id: Annotated[UserId, Depends(get_current_user_id)],
    service: Annotated[
        ListUserPlansService,
        Depends(get_list_user_plans_service),
    ],
) -> list[PlanResponse]:
    results = await service.execute(
        ListUserPlansQuery(user_id=user_id.value),
    )

    return [_to_response(plan) for plan in results]


@router.get(
    "/{plan_id}",
    response_model=PlanResponse,
    status_code=status.HTTP_200_OK,
)
async def get_plan(
    plan_id: UUID,
    user_id: Annotated[UserId, Depends(get_current_user_id)],
    service: Annotated[
        GetPlanService,
        Depends(get_get_plan_service),
    ],
) -> PlanResponse:
    result = await service.execute(
        GetPlanByIdQuery(
            user_id=user_id.value,
            plan_id=plan_id,
        ),
    )

    return _to_response(result)


@router.patch(
    "/{plan_id}",
    response_model=PlanResponse,
    status_code=status.HTTP_200_OK,
)
async def update_plan(
    plan_id: UUID,
    request: UpdatePlanRequest,
    user_id: Annotated[UserId, Depends(get_current_user_id)],
    service: Annotated[
        UpdatePlanService,
        Depends(get_update_plan_service),
    ],
) -> PlanResponse:
    result = await service.execute(
        UpdatePlanCommand(
            user_id=user_id.value,
            plan_id=plan_id,
            expected_version=request.version,
            name=request.name,
            description=request.description,
        ),
    )

    return _to_response(result)


@router.post(
    "/{plan_id}/publish",
    response_model=PlanResponse,
    status_code=status.HTTP_200_OK,
)
async def publish_plan(
    plan_id: UUID,
    user_id: Annotated[UserId, Depends(get_current_user_id)],
    service: Annotated[
        ChangePlanStatusService,
        Depends(get_change_plan_status_service),
    ],
) -> PlanResponse:
    result = await service.execute(
        ChangePlanStatusCommand(
            user_id=user_id.value,
            plan_id=plan_id,
            action=PlanStatusAction.PUBLISH,
        ),
    )

    return _to_response(result)


@router.post(
    "/{plan_id}/archive",
    response_model=PlanResponse,
    status_code=status.HTTP_200_OK,
)
async def archive_plan(
    plan_id: UUID,
    user_id: Annotated[UserId, Depends(get_current_user_id)],
    service: Annotated[
        ChangePlanStatusService,
        Depends(get_change_plan_status_service),
    ],
) -> PlanResponse:
    result = await service.execute(
        ChangePlanStatusCommand(
            user_id=user_id.value,
            plan_id=plan_id,
            action=PlanStatusAction.ARCHIVE,
        ),
    )

    return _to_response(result)
