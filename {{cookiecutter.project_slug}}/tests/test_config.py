from app.core.config import get_settings


def test_settings_are_loaded() -> None:
    settings = get_settings()

    assert settings.app_name == "{{cookiecutter.project_name}}-test"
    assert settings.app_env == "test"
    assert settings.debug is False
