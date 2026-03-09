"""
Application configuration via environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "DevBrain"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # --- Security ---
    SECRET_KEY: str = "change-me-in-production-super-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    ALGORITHM: str = "HS256"

    # --- Database ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./devbrain.db"

    # --- GitHub OAuth ---
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # --- OpenRouter / AI ---
    OPENROUTER_API_KEY: str = ""
    AI_MODEL: str = "google/gemma-3-4b-it"

    # --- CORS ---
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # --- AWS / Snowflake Landing Zone ---
    AWS_ACCESS_KEY: str = ""
    AWS_SECRET_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str = "devbrain-raw-events"


settings = Settings()
