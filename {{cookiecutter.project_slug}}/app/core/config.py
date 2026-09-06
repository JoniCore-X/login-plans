from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "{{cookiecutter.project_name}}"
    app_env: str = "development"
    debug: bool = False
    database_url: SecretStr
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    redis_url: str | None = None
    otlp_endpoint: str | None = None
    enable_tracing: bool = True
    resend_api_key: str | None = None
    email_from: str = "noreply@example.com"
    email_verify_base_url: str = "http://localhost:8000/api/v1/auth/verify-email"

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.test"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
