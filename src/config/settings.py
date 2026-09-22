"""Centralized configuration loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for notebooks, scripts, and FastAPI."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = Field(
        "sqlite:///./data/processed/lab_attendance.db", alias="DATABASE_URL"
    )
    face_recognition_threshold: float = Field(0.55, alias="FACE_RECOGNITION_THRESHOLD")
    camera_index: int = Field(0, alias="CAMERA_INDEX")
    cooldown_seconds: int = Field(10, alias="COOLDOWN_SECONDS")
    model_name: str = Field("buffalo_l", alias="MODEL_NAME")
    log_level: str = Field("INFO", alias="LOG_LEVEL")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings so the application reads .env only once."""

    return Settings()
