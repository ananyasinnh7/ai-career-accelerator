"""
app/core/config.py
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Groq ───────────────────────────────────────────────────────────────────
    groq_api_key: str = ""

    # ── Google Gemini (kept for future use) ────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model:   str = "gemini-2.0-flash"

    # ── Database ───────────────────────────────────────────────────────────────
    database_url: str = "sqlite:///./career_accelerator.db"

    # ── App ────────────────────────────────────────────────────────────────────
    app_env:            str = "development"
    log_level:          str = "INFO"
    max_pdf_size_bytes: int = 10 * 1024 * 1024

    # ── Auth ───────────────────────────────────────────────────────────────────
    secret_key:                  str = "change-me-in-production"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days:   int = 7
    algorithm:                   str = "HS256"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()