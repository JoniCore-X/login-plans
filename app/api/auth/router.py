from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    UserResponse,
)
from app.api.dependencies import (
    get_login_user_service,
    get_register_user_service,
)
from app.application.users.commands import (
    LoginUserCommand,
    RegisterUserCommand,
)
from app.application.users.services import (
    LoginUserService,
    RegisterUserService,
)

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
        status=user.status,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    request: LoginRequest,
    service: Annotated[
        LoginUserService,
        Depends(get_login_user_service),
    ],
) -> LoginResponse:
    result = await service.execute(
        LoginUserCommand(
            email=request.email,
            password=request.password,
        ),
    )

    return LoginResponse(
        user_id=result.user_id,
        session_id=result.session_id,
        expires_at=result.expires_at,
    )
