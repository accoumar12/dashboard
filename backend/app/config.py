"""Application configuration."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings.

    Configuration for the SQL Dashboard backend application.
    Settings are loaded from environment variables with the APP_ prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    database_url: str = "postgresql://postgres:postgres@localhost:5432/dashboard"
    use_playground_db: bool = True  # Use SQLite playground if PostgreSQL unavailable
    playground_db_path: str = str(Path(__file__).parent.parent / "playground.db")
    allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Upload settings
    upload_dir: Path = Path(__file__).parent.parent / "uploads"
    max_upload_size_mb: int = 50
    session_expiry_days: int = 7
    cleanup_interval_hours: int = 6
    query_timeout_seconds: int = 30

    debug: bool = False


settings = Settings()
