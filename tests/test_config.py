from app.core.config import get_settings


def test_settings_are_loaded() -> None:
    settings = get_settings()

    assert settings.app_name == "login-plans"
    assert settings.app_env == "development"
    assert settings.debug is True
