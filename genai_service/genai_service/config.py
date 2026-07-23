"""Application configuration via environment variables."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from .env / environment."""

    model_config = SettingsConfigDict(
        env_file=(".env", "genai_service/.env", "genai_service/genai_service/.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "GenAI Interview Service"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"
    service_port: int = 8100

    # LLM (Groq)
    groq_api_key: str | None = None  # SDK auto-reads GROQ_API_KEY from env
    groq_model: str = "llama-3.3-70b-versatile"
    groq_fallback_model: str = "llama-3.1-8b-instant"
    llm_temperature: float = 0.3
    llm_max_retries: int = 3
    llm_timeout_seconds: int = 60

    # Interview rules
    max_questions: int = Field(default=15, ge=1, le=50)
    interview_time_limit_minutes: int = Field(default=30, ge=5, le=180)
    difficulty_increase_threshold: float = 85.0
    difficulty_decrease_threshold: float = 60.0

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    @property
    def active_model(self) -> str:
        return self.groq_model


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Force reload settings from .env on next access."""
    global _settings
    _settings = None
