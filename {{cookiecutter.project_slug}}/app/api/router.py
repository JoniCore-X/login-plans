from collections.abc import Awaitable
from typing import cast

from fastapi import APIRouter, Depends, Response

from app.api.auth.router import router as auth_router
from app.api.dependencies import (
    get_app_settings,
    get_application_container,
)
from app.api.plans.router import router as plans_router
from app.api.schemas.health import HealthResponse
from app.bootstrap.container import ApplicationContainer
from app.core.config import Settings

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)
router.include_router(plans_router)


@router.get("/health", response_model=HealthResponse)
async def health_check(
    response: Response,
    container: ApplicationContainer = Depends(get_application_container),  # noqa: B008
) -> HealthResponse:
    components: dict[str, str] = {}

    is_db_healthy = await container.health_checker.is_healthy()
    components["database"] = "connected" if is_db_healthy else "disconnected"

    if container.redis_client is not None:
        try:
            await cast(
                Awaitable[bool],
                container.redis_client.ping(),
            )
            components["redis"] = "connected"
        except Exception:
            components["redis"] = "disconnected"

    healthy = all(value == "connected" for value in components.values())

    if not healthy:
        response.status_code = 503

    return HealthResponse(
        status="healthy" if healthy else "unhealthy",
        components=components,
    )


@router.get("/")
async def root(
    settings: Settings = Depends(get_app_settings),  # noqa: B008
) -> dict[str, str]:
    return {
        "application": settings.app_name,
        "version": "v1",
    }
