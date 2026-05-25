from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    # App
    app_name: str = "Health Insurance Platform"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql://user:password@localhost:5432/health_insurance"
    database_pool_size: int = 20
    database_max_overflow: int = 10
    database_echo: bool = False

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600

    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"

    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    cors_credentials: bool = True
    cors_methods: list = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    cors_headers: list = ["Authorization", "Content-Type", "X-Tenant-ID", "Accept"]

    # Celery
    celery_broker_url: str = "amqp://user:password@localhost:5672/"
    celery_result_backend: str = "redis://localhost:6379/1"

    # Logging
    log_level: str = "INFO"

    # Encryption
    encryption_key: str = "your-encryption-key-change-in-production"

    # Email / SMTP (leave SMTP_HOST empty to use dev-mode logging instead of sending)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@healthinsurance.local"

    # Frontend URL (used in password-reset emails)
    frontend_url: str = "http://localhost:5173"

    # Rate limiting (login attempts per minute per IP)
    login_rate_limit: int = 10

    # Feature flags
    enable_claims: bool = True
    enable_government_integration: bool = False
    enable_batch_processing: bool = False

    model_config = SettingsConfigDict(env_file=Path(__file__).parent / ".env", case_sensitive=False)


@lru_cache()
def get_settings() -> Settings:
    return Settings()
