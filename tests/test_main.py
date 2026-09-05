from fastapi import FastAPI

from app.main import create_application


def test_create_application() -> None:
    application = create_application()

    assert isinstance(application, FastAPI)
    assert application.title == "login-plans-test"
