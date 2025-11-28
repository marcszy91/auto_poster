"""Application configuration using Pydantic Settings."""

from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./auto_poster.db"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    cors_origins: Union[List[str], str] = "http://localhost:5173,http://localhost:3000"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[List[str], str]) -> List[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # File Upload Configuration
    max_upload_size: int = 10485760  # 10MB
    upload_dir: str = "./uploads"
    temp_dir: str = "./temp"

    # Video Generation Settings
    video_duration: int = 15  # Instagram Reels duration in seconds
    shorts_duration: int = 60  # YouTube Shorts duration in seconds

    # MakerWorld Scraper Settings
    makerworld_base_url: str = "https://makerworld.com"
    scraper_timeout: int = 30
    headless_browser: bool = True

    # Authentication & Security
    jwt_secret_key: str = ""  # Loaded from database on startup (auto-generated)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Admin User Configuration (for initial setup)
    admin_email: str = ""
    admin_password: str = ""

    # SMTP Email Configuration
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Auto Poster"
    smtp_use_tls: bool = True

    # Logging Configuration
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_format: str = "text"  # text or json (for Datadog, CloudWatch, etc.)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
