from fastapi import FastAPI

from app.bootstrap.application import Application
from app.core.config import Settings


def test_create_application(
    test_settings: Settings,
) -> None:
    application = Application(
        test_settings,
    )

    app = application.create()

    assert isinstance(app, FastAPI)
    assert app.title == "{{cookiecutter.project_name}}-test"
