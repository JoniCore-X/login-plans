from app.bootstrap.application import Application
from app.core.config import get_settings

settings = get_settings()

app = Application(settings).create()
