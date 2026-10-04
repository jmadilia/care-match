from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    PROJECT_NAME: str = "FastAPI Backend"
    ENVIRONMENT: str = "local"
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5433/app"

    # Comma-separated list of allowed origins, e.g. "http://localhost:3000,https://example.com"
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000"

    # The CRUD and strategy-run routers are an admin surface, not part of the public API.
    # Unset, they are mounted only when ENVIRONMENT is "local", so a deployed instance exposes
    # nothing but health, comparisons, and intake without any extra configuration.
    ADMIN_API_ENABLED: bool | None = None
    # When set, admin routes require this value in an X-Admin-Key header.
    ADMIN_API_KEY: str | None = None

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def admin_api_enabled(self) -> bool:
        if self.ADMIN_API_ENABLED is not None:
            return self.ADMIN_API_ENABLED
        return self.ENVIRONMENT == "local"

    @model_validator(mode="after")
    def _admin_api_outside_local_needs_a_key(self) -> Self:
        if self.admin_api_enabled and self.ENVIRONMENT != "local" and not self.ADMIN_API_KEY:
            raise ValueError("ADMIN_API_ENABLED outside ENVIRONMENT=local requires ADMIN_API_KEY")
        return self


settings = Settings()
