from fastapi import APIRouter, Depends

from app.api.auth.router import router as auth_router
from app.api.dependencies import get_app_settings
from app.api.schemas.health import HealthResponse
from app.core.config import Settings

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router)


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
    )


@router.get("/")
async def root(
    settings: Settings = Depends(get_app_settings),  # noqa: B008
) -> dict[str, str]:
    return {
        "application": settings.app_name,
        "version": "v1",
    }
