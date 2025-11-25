"""
Application configuration using Pydantic Settings.
Loads settings from environment variables and .env file.
"""

from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="allow"
    )

    # Application
    APP_NAME: str = "RSS News Aggregator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # API
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8081",
        "http://localhost:19006",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 50
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300  # 5 minutes

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_BEAT_SCHEDULE_INTERVAL: int = 900  # 15 minutes in seconds

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Validate SECRET_KEY meets security requirements."""
        # Allow test keys that explicitly contain 'test' or 'testing'
        is_test_key = "test" in v.lower() or "testing" in v.lower()

        if not is_test_key and len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters for security. "
                'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
            )

        # Check for common insecure defaults (but allow test keys)
        if not is_test_key:
            insecure_defaults = ["your-secret-key-here", "changeme", "password"]
            if any(default in v.lower() for default in insecure_defaults):
                raise ValueError(
                    "SECRET_KEY contains insecure default value. "
                    'Generate a secure key with: python -c "import secrets; print(secrets.token_urlsafe(32))"'
                )
        return v

    # OAuth (Optional)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    APPLE_CLIENT_ID: Optional[str] = None
    APPLE_CLIENT_SECRET: Optional[str] = None

    # Supabase (Optional)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # RSS Feed Settings
    RSS_FETCH_TIMEOUT: int = 10
    RSS_MAX_CONCURRENT_FETCHES: int = 5
    RSS_USER_AGENT: str = "RSS-News-Aggregator/1.0"

    # Fact-Check API Settings
    FACT_CHECK_API_URL: str = "https://fact-check-production.up.railway.app"
    FACT_CHECK_ENABLED: bool = True
    FACT_CHECK_MODE: str = "summary"  # standard, thorough, summary, or synthesis
    FACT_CHECK_POLL_INTERVAL: int = 5  # seconds between status polls
    FACT_CHECK_MAX_POLL_ATTEMPTS: int = 180  # max polling attempts (15 minutes at 5s intervals)
    # Note: Synthesis mode requires 4-7 minutes, thorough 5-10 minutes, standard ~1 minute
    # 180 attempts × 5s = 900s (15 min) accommodates all modes with buffer
    FACT_CHECK_MAX_WAIT: int = (
        120  # maximum wait time (2 minutes) - DEPRECATED, use MAX_POLL_ATTEMPTS
    )
    FACT_CHECK_RETRY_ATTEMPTS: int = 3  # max retry attempts on failure

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_UNAUTHENTICATED: int = 20
    
    # Email Settings (SMTP - Legacy)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@example.com"
    SMTP_FROM_NAME: str = "RSS News Aggregator"
    SMTP_USE_TLS: bool = True
    
    # Microsoft Graph API Settings (Preferred for production)
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_TENANT_ID: Optional[str] = None
    MICROSOFT_SENDER_EMAIL: Optional[str] = None  # Outlook/Office 365 email address
    MICROSOFT_SENDER_NAME: str = "RSS News Aggregator"
    USE_GRAPH_API: bool = False  # Set to True to use Microsoft Graph API instead of SMTP
    
    # Email Verification
    EMAIL_VERIFICATION_REQUIRED: bool = False  # Set to True to enforce verification
    FRONTEND_URL: str = "http://localhost:3000"  # For verification links
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 1

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text

    # Error Tracking (Sentry)
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1  # 10% of transactions

    # Admin User (for initial setup - MUST be provided via environment)
    ADMIN_EMAIL: str
    ADMIN_USERNAME: str
    ADMIN_PASSWORD: str

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

    def validate_production_config(self) -> None:
        """Validate configuration for production deployment."""
        if not self.is_production:
            return

        errors = []

        # Check DEBUG is disabled
        if self.DEBUG:
            errors.append("DEBUG must be False in production")

        # Check CORS origins are not localhost
        localhost_origins = ["localhost", "127.0.0.1", "0.0.0.0"]
        for origin in self.BACKEND_CORS_ORIGINS:
            if any(local in origin for local in localhost_origins):
                errors.append(
                    f"CORS origin '{origin}' contains localhost - not suitable for production"
                )

        # Check admin credentials are set (already enforced by Pydantic, but good to check)
        if not self.ADMIN_EMAIL or not self.ADMIN_USERNAME or not self.ADMIN_PASSWORD:
            errors.append("Admin credentials must be set via environment variables")

        # Check SECRET_KEY is strong (additional check beyond validator)
        if len(self.SECRET_KEY) < 32:
            errors.append("SECRET_KEY must be at least 32 characters")

        if errors:
            error_msg = "Production configuration validation failed:\n" + "\n".join(
                f"  - {e}" for e in errors
            )
            raise ValueError(error_msg)


# Global settings instance
settings = Settings()
