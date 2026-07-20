"""Application configuration loaded from environment."""

from __future__ import annotations

from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database ---
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/portfolio_engine"
    database_url_sync: str = "postgresql://postgres:postgres@localhost:5432/portfolio_engine"

    # --- API Keys ---
    alpha_vantage_key: str = ""
    finnhub_key: str = ""
    polygon_key: str = ""
    fmp_key: str = ""

    # --- Reddit ---
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "portfolio-engine/1.0"

    # --- LLM ---
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # --- Vector DB ---
    chroma_persist_dir: str = "./data/chromadb"

    # --- Celery ---
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # --- App ---
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def has_alpha_vantage(self) -> bool:
        return bool(self.alpha_vantage_key)

    @property
    def has_finnhub(self) -> bool:
        return bool(self.finnhub_key)

    @property
    def has_polygon(self) -> bool:
        return bool(self.polygon_key)

    @property
    def has_fmp(self) -> bool:
        return bool(self.fmp_key)

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_reddit(self) -> bool:
        return bool(self.reddit_client_id and self.reddit_client_secret)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
