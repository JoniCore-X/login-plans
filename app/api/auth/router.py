from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.auth.schemas import (
    RegisterRequest,
    UserResponse,
)
from app.api.dependencies import get_register_user_service
from app.application.commands.register_user import RegisterUserCommand
from app.application.services.register_user import RegisterUserService

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: RegisterRequest,
    service: Annotated[
        RegisterUserService,
        Depends(get_register_user_service),
    ],
) -> UserResponse:
    command = RegisterUserCommand(
        email=request.email,
        password=request.password,
    )

    user = await service.execute(command)

    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
