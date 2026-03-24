"""
Configuration management for QuizSensei.
Handles environment variables, path management, and app-wide settings.
"""
from functools import lru_cache
from pathlib import Path
from typing import List, Set

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Application ───────────────────────────────────────────────────────
    APP_NAME: str = "QuizSensei"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    UPLOAD_DIR: Path = Path("uploads")
    EXTRACTED_DIR: Path = Path("uploads/extracted")
    ANALYSIS_DIR: Path = Path("uploads/analysis")
    QUESTIONS_DIR: Path = Path("uploads/questions")
    # Maximum file size in bytes (default: 20 MB)
    MAX_FILE_SIZE_BYTES: int = 20 * 1024 * 1024
    # Allowed MIME types (enforced alongside extension check)
    ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".txt", ".docx"}

    # ── OpenRouter LLM ───────────────────────────────────────────────────
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str
    OPENROUTER_API_KEYS: str
    
    # ── Database (PostgreSQL) ────────────────────────────────────────────
    POSTGRES_USER: str = "quizsensei"
    POSTGRES_PASSWORD: str = "quizsensei_secret"
    POSTGRES_DB: str = "quizsensei_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    @property
    def database_url(self) -> str:
        """Constructs the async SQLAlchemy database URL."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # ── Cache / Workers (Redis) ──────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # Comma-separated list of API keys for round-robin/random rotation
    # This helps stay within rate limits for free-tier endpoints.
    @property
    def openrouter_keys_list(self) -> List[str]:
        """Return the parsed list of non-empty OpenRouter API keys."""
        if not self.OPENROUTER_API_KEYS:
            return []
        return [k.strip() for k in self.OPENROUTER_API_KEYS.split(",") if k.strip()]

    # ── Pydantic-settings config ───────────────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def ensure_upload_dir(self) -> None:
        """Create the necessary storage directories if they do not exist."""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
        self.ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
        self.QUESTIONS_DIR.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()
