from functools import lru_cache
from typing import cast

from fastapi import Request

from app.application.auth.services import (
    AuthenticationService,
    LogoutService,
    RotateSessionService,
)
from app.application.users.services import (
    GetUserService,
    LoginUserService,
    RegisterUserService,
)
from app.bootstrap.container import ApplicationContainer
from app.core.config import Settings, get_settings


@lru_cache
def get_app_settings() -> Settings:
    return get_settings()


def get_application_container(
    request: Request,
) -> ApplicationContainer:
    return cast(ApplicationContainer, request.app.state.container)


def get_register_user_service(
    request: Request,
) -> RegisterUserService:
    container = get_application_container(request)

    return container.create_register_user_service()


def get_login_user_service(
    request: Request,
) -> LoginUserService:
    container = get_application_container(request)

    return container.create_login_user_service()


def get_authentication_service(
    request: Request,
) -> AuthenticationService:
    container = get_application_container(request)

    return container.create_authentication_service()


def get_logout_service(
    request: Request,
) -> LogoutService:
    container = get_application_container(request)

    return container.create_logout_service()


def get_rotate_session_service(
    request: Request,
) -> RotateSessionService:
    container = get_application_container(request)

    return container.create_rotate_session_service()


def get_get_user_service(
    request: Request,
) -> GetUserService:
    container = get_application_container(request)

    return container.create_get_user_service()
