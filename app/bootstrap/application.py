import logging

from app.core.config import Settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)


class Application:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def start(self) -> None:
        configure_logging(self.settings.debug)

        logger.info(
            "Application started: %s",
            self.settings.app_name,
        )

    def stop(self) -> None:
        logger.info("Application stopped")
