from fastapi import Request
from fastapi.responses import JSONResponse

from app.domain.exceptions.base import DomainError
from app.domain.exceptions.user import (
    InvalidEmailError,
    UserAlreadyExistsError,
    UserNotFoundError,
)


async def user_already_exists_handler(
    request: Request,
    exc: UserAlreadyExistsError,
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "error": {
                "code": "USER_ALREADY_EXISTS",
                "message": str(exc),
            },
        },
    )


async def user_not_found_handler(
    request: Request,
    exc: UserNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "USER_NOT_FOUND",
                "message": str(exc),
            },
        },
    )


async def invalid_email_handler(
    request: Request,
    exc: InvalidEmailError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "INVALID_EMAIL",
                "message": str(exc),
            },
        },
    )


async def domain_error_handler(
    request: Request,
    exc: DomainError,
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "DOMAIN_ERROR",
                "message": str(exc),
            },
        },
    )
