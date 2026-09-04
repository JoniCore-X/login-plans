import logging

from fastapi import FastAPI

from app.api.router import router
from app.core.config import Settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


class Application:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def create(self) -> FastAPI:
        configure_logging(self.settings.debug)

        application = FastAPI(
            title=self.settings.app_name,
            debug=self.settings.debug,
        )

        application.include_router(router)

        logger.info(
            "Application created: %s",
            self.settings.app_name,
        )

        return application
