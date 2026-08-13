"""Configuration objects for the Whitfield WMS backend.

Centralizes environment-driven settings so the rest of the codebase reads
strongly-typed values instead of raw environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment / ``.env``."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Whitfield WMS API"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/v1"

    secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "whitfield_wms"

    enable_scheduler: bool = True

    # ---- AI (chatbot / voice) ----
    # Groq is the LLM provider (OpenAI-compatible). Get a key at https://console.groq.com
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    notification_email_from: str = "notifications@whitfieldfulfillment.com"


settings = Settings()
