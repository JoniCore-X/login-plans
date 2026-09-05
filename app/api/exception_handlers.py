from fastapi import Request
from fastapi.responses import JSONResponse


async def user_already_exists_handler(
    request: Request,
    exc: Exception,
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
    exc: Exception,
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
    exc: Exception,
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


async def invalid_credentials_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid credentials.",
            },
        },
    )


async def user_cannot_authenticate_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "error": {
                "code": "AUTHENTICATION_NOT_ALLOWED",
                "message": "Authentication is not available for this account.",
            },
        },
    )


async def domain_error_handler(
    request: Request,
    exc: Exception,
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
