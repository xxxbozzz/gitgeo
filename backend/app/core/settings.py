"""Typed backend settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_name: str = "GEO Backend"
    app_version: str = "0.2.0"
    app_env: str = "development"
    app_debug: bool = False
    api_prefix: str = "/api/v1"

    # PostgreSQL
    db_host: str = "localhost"
    db_port: int = 5432
    db_user: str = "geo_app"
    db_password: str = "change-this-password"
    db_name: str = "geo_engine"
    db_pool_size: int = 10
    db_max_overflow: int = 5

    # Frontend
    frontend_dist_dir: str = "/app/frontend_dist"

    # Publishing
    article_action_timeout_seconds: int = 120
    publish_request_timeout_seconds: int = 20
    enable_live_publish: bool = False

    # LLM
    llm_fix_max_tokens: int = 8000

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
