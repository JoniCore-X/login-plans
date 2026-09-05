from fastapi import APIRouter, Depends, Response

from app.api.auth.router import router as auth_router
from app.api.dependencies import (
    get_app_settings,
    get_application_container,
)
from app.api.schemas.health import HealthResponse
from app.bootstrap.container import ApplicationContainer
from app.core.config import Settings

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)


@router.get("/health", response_model=HealthResponse)
async def health_check(
    response: Response,
    container: ApplicationContainer = Depends(get_application_container),  # noqa: B008
) -> HealthResponse:
    is_db_healthy = await container.health_checker.is_healthy()

    if not is_db_healthy:
        response.status_code = 503

        return HealthResponse(
            status="unhealthy",
            components={"database": "disconnected"},
        )

    return HealthResponse(
        status="healthy",
        components={"database": "connected"},
    )


@router.get("/")
async def root(
    settings: Settings = Depends(get_app_settings),  # noqa: B008
) -> dict[str, str]:
    return {
        "application": settings.app_name,
        "version": "v1",
    }
