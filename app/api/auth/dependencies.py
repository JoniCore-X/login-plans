from typing import Annotated

from fastapi import Depends, Header, Request

from app.api.dependencies import (
    get_application_container,
    get_authentication_service,
)
from app.application.auth.dto import AuthenticatedUser
from app.application.auth.exceptions import (
    AuthenticationError,
    RateLimitExceededError,
)
from app.application.auth.services import AuthenticationService

_BEARER_PREFIX = "Bearer "


def get_bearer_credential(
    authorization: Annotated[
        str | None,
        Header(),
    ] = None,
) -> str:
    if authorization is None:
        raise AuthenticationError(
            "Authentication failed.",
        )

    if not authorization.startswith(_BEARER_PREFIX):
        raise AuthenticationError(
            "Authentication failed.",
        )

    credential = authorization[len(_BEARER_PREFIX) :].strip()

    if not credential:
        raise AuthenticationError(
            "Authentication failed.",
        )

    return credential


async def enforce_login_rate_limit(
    request: Request,
) -> None:
    container = get_application_container(request)

    client_host = request.client.host if request.client is not None else "unknown"

    allowed = await container.rate_limiter.allow(
        f"login:{client_host}",
    )

    if not allowed:
        raise RateLimitExceededError(
            "Too many login attempts.",
        )


async def get_authenticated_user(
    credential: Annotated[
        str,
        Depends(get_bearer_credential),
    ],
    service: Annotated[
        AuthenticationService,
        Depends(get_authentication_service),
    ],
) -> AuthenticatedUser:
    return await service.authenticate(
        credential,
    )
