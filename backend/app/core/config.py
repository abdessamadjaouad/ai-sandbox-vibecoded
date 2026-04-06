# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Sandbox"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "info"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aisandbox"
    mlflow_tracking_uri: str = "http://localhost:5000"

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_name: str = "sandbox"
    minio_secure: bool = False

    chroma_host: str = "localhost"
    chroma_port: int = 8000

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    default_random_seed: int = 42


settings = Settings()
