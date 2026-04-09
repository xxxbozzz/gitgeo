"""Typed backend settings."""

from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "GEO Backend"
    app_version: str = "0.1.0"
    app_env: str = "development"
    app_debug: bool = False
    api_prefix: str = "/api/v1"

    db_host: str = "mysql_db"
    db_port: int = 3306
    db_user: str = "geo_app"
    db_password: str = "change-this-password"
    db_name: str = "geo_engine"
    db_pool_name: str = "geo_backend_pool"
    db_pool_size: int = 5
    article_action_timeout_seconds: int = 120
    publish_request_timeout_seconds: int = 20
    llm_fix_max_tokens: int = 8000

    @property
    def sqlalchemy_database_url(self) -> str:
        """Return a SQLAlchemy-compatible MySQL URL."""
        password = quote_plus(self.db_password)
        return (
            f"mysql+mysqlconnector://{self.db_user}:{password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
