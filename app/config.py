"""
Configuration for the Member 6 Alert & Notification module.

Everything is read from environment variables so this module can be wired
into whatever configuration mechanism the rest of the ThreatLens AI project
ends up using (e.g. a shared .env / pydantic Settings object). Nothing is
hardcoded.

INTEGRATION NOTE: If the team already has a central settings module by the
time this is merged, replace this file with an import from that module
instead of maintaining a second source of config.
"""
import os
from dataclasses import dataclass


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # Database (defaults to local SQLite so the module runs standalone for
    # dev/testing without requiring PostgreSQL to be running. Set
    # ALERTS_DATABASE_URL to the project's real PostgreSQL DSN in staging/prod).
    database_url: str = os.getenv(
        "ALERTS_DATABASE_URL", "sqlite:///./member6_alerts.db"
    )

    # JWT (placeholder — see app/auth/dependencies.py). Must match whatever
    # secret Member 1's real auth service issues tokens with.
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    auth_enabled: bool = _get_bool("ALERTS_AUTH_ENABLED", True)

    # SMTP / email notification settings
    smtp_host: str = os.getenv("SMTP_HOST", "")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_use_tls: bool = _get_bool("SMTP_USE_TLS", True)
    alert_from_email: str = os.getenv("ALERT_FROM_EMAIL", "alerts@threatlens.local")

    # When no SMTP host is configured (e.g. local dev), fall back to a
    # console notifier instead of failing.
    notifications_enabled: bool = _get_bool("NOTIFICATIONS_ENABLED", True)


settings = Settings()
