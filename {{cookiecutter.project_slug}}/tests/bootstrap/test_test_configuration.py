from app.core.config import Settings


def test_test_environment_is_used(test_settings: Settings) -> None:
    assert test_settings.app_env == "test"


def test_test_database_is_not_the_development_database(
    test_settings: Settings,
) -> None:
    database_url = test_settings.database_url.get_secret_value()

    assert "{{cookiecutter.project_slug}}_test" in database_url
    assert "localhost:5432" in database_url
