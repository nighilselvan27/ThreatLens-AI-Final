"""
Centralized configuration for the Alert & Notification Module.
Reads values from environment variables / a .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/malware_platform"

    # SMTP
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "Malware Detection Platform"
    smtp_use_tls: bool = True

    # Auth
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"

    # Optional integrations
    virustotal_api_key: str = ""

    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
