"""
Application configuration using Pydantic Settings.

Centralizes all application settings with environment variable support,
type validation, and sensible defaults for development.

Key components:
    - Settings: Pydantic BaseSettings class with all configuration
    - settings: Global singleton instance
    - Environment groups: App, API, CORS, PostgreSQL, MongoDB, Telegram

Dependencies:
    - pydantic-settings: Settings management with env var support
    - python-dotenv: Load .env file

Related files:
    - .env: Environment-specific overrides (not in git)
    - .env.example: Template with all available settings
    - docker-compose.yml: Container environment configuration

Common commands:
    - Create config: cp .env.example .env
    - Generate secret: python -c "import secrets; print(secrets.token_hex(32))"

Example:
    Accessing settings::

        from app.config import settings

        # Application settings
        print(settings.APP_NAME)
        print(settings.ENVIRONMENT)  # "development", "staging", "production"

        # Database URLs
        print(settings.postgres_url)
        print(settings.MONGODB_URL)

        # Helper properties
        if settings.is_production:
            # Production-specific logic
            ...

    Environment variables::

        # .env file
        APP_NAME=MyApp
        ENVIRONMENT=production
        DEBUG=false
        SECRET_KEY=your-secret-key-here
        POSTGRES_SERVER=localhost
        POSTGRES_USER=app_user
        POSTGRES_PASSWORD=secret
        POSTGRES_DB=myapp

Setting categories:
    - Application: APP_NAME, APP_VERSION, ENVIRONMENT, DEBUG, LOG_LEVEL
    - API Security: SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
    - CORS: CORS_ORIGINS, CORS_CREDENTIALS, CORS_METHODS, CORS_HEADERS
    - PostgreSQL: POSTGRES_SERVER, POSTGRES_PORT, POSTGRES_USER, etc.
    - MongoDB: MONGODB_URL, MONGODB_DB, pool settings
    - Alerts: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ALERTS_ENABLED
"""
from typing import Any, Literal
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    # CONFIGURATION: Update these default values for your project.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # =========================================================================
    # Application Settings
    # CONFIGURATION: Update these for your project
    # =========================================================================
    APP_NAME: str = "FastAPI Boilerplate"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # =========================================================================
    # API Settings
    # =========================================================================
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str  # REQUIRED: Generate with `openssl rand -hex 32`
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER_ME: int = 30  # For "remember me" feature

    # =========================================================================
    # Cookie Settings (for httpOnly cookies)
    # =========================================================================
    COOKIE_SECURE: bool = False  # Set to True in production (HTTPS only)
    COOKIE_SAMESITE: str = "lax"  # lax, strict, or none
    COOKIE_DOMAIN: str | None = None  # For subdomains if needed

    # =========================================================================
    # CORS Settings
    # CONFIGURATION: Update for your frontend URLs
    # =========================================================================
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    # =========================================================================
    # PostgreSQL Settings
    # NOTE: If not using PostgreSQL, see README for removal instructions
    # =========================================================================
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_POOL_SIZE: int = 5
    POSTGRES_MAX_OVERFLOW: int = 10

    @property
    def postgres_url(self) -> str:
        """Build PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # =========================================================================
    # MongoDB Settings
    # NOTE: If not using MongoDB, see README for removal instructions
    # =========================================================================
    MONGODB_URL: str
    MONGODB_DB: str
    MONGODB_MIN_POOL_SIZE: int = 5
    MONGODB_MAX_POOL_SIZE: int = 50

    # =========================================================================
    # Telegram Alerts (Optional)
    # NOTE: If not using alerts, see app/core/alerts.py for removal instructions
    # =========================================================================
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None
    TELEGRAM_ALERTS_ENABLED: bool = False

    # =========================================================================
    # Helper Properties
    # =========================================================================
    @property
    def access_token_expires_seconds(self) -> int:
        """Access token expiration in seconds."""
        return self.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    @property
    def refresh_token_expires_seconds(self) -> int:
        """Refresh token expiration in seconds."""
        return self.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    @property
    def refresh_token_remember_me_expires_seconds(self) -> int:
        """Refresh token expiration for 'remember me' in seconds."""
        return self.REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER_ME * 24 * 60 * 60

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"


# Global settings instance
settings = Settings()
