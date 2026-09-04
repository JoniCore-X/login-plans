from fastapi import FastAPI

from app.bootstrap.application import Application
from app.core.config import get_settings


def create_application() -> FastAPI:
    settings = get_settings()

    application = Application(settings)

    return application.create()


app = create_application()
