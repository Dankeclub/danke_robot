"""Application settings loaded from environment / .env file."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global application settings.

    Attributes:
        app_env: Runtime environment name (dev, test, prod).
        log_level: Logging level.
        database_url: Async PostgreSQL connection URL using asyncpg.
        jwt_secret: Secret key for signing JWT tokens.
        jwt_algorithm: JWT signing algorithm.
        access_token_ttl_seconds: Access token time-to-live in seconds.
        refresh_token_ttl_seconds: Refresh token time-to-live in seconds.
        wx_appid: WeChat Mini Program AppID.
        wx_secret: WeChat Mini Program AppSecret.
        phone_login_rate_limit: Max phone login attempts per IP per minute.
        business_timezone: IANA timezone for business date calculations.
    """

    app_env: str = "dev"
    log_level: str = "INFO"
    database_url: str = "postgresql+asyncpg://parent:parent@localhost:5432/parent_db"

    # JWT
    jwt_secret: SecretStr = SecretStr("change-me-in-production")
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 7200
    refresh_token_ttl_seconds: int = 2592000

    # WeChat Mini Program
    wx_appid: str = ""
    wx_secret: SecretStr = SecretStr("")

    # Rate limiting
    phone_login_rate_limit: int = 5

    # Business
    business_timezone: str = "Asia/Shanghai"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
