"""Centralized configuration via pydantic-settings.

All settings are read from environment variables (or .env file). This is the
single source of truth for configuration across the backend.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "Coptic Dictionary & Translator"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"
    SEED_ON_STARTUP: bool = True

    # --- Database ---
    DATABASE_URL: str = (
        "postgresql+psycopg://coptic:coptic_pass@localhost:5432/coptic_dic"
    )
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- JWT / Auth ---
    JWT_SECRET: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # --- CORS ---
    BACKEND_CORS_ORIGINS: list[str] | str = ["*"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def _split_cors(cls, v):  # noqa: ANN001
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # --- Embeddings / RAG ---
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIM: int = 384
    EMBEDDING_ENABLED: bool = True

    # --- LLM (optional, gated) ---
    LLM_PROVIDER: Literal["none", "openai", "ollama"] = "none"
    OPENAI_API_KEY: str = ""

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_testing(self) -> bool:
        return os.getenv("PYTEST_CURRENT_TEST") is not None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
