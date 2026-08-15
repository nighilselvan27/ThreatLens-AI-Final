"""
Configuration for the Alert & Notification Module.

ASSUMPTION / TODO FOR MEMBER 8:
Member 1 (User Management / Database Design) has not yet published a
project-wide settings module (`backend/app/config/` is still empty), so
this module reads its own environment variables, scoped with an `ALERT_`
awareness of the *shared* variables (DATABASE_URL, JWT_*) that every
other module will also need.

Once Member 1 delivers a shared `backend/app/config/settings.py`, this
file should be deleted and the alerts module should import the shared
`Settings` object instead. Nothing else in this module needs to change
as long as the shared settings object exposes the same attribute names
used below (see the mapping table in this module's README.md).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AlertSettings(BaseSettings):
    # --- Database (shared with the rest of the platform) ---
    database_url: str = "postgresql://user:password@localhost:5432/malware_platform"

    # --- SMTP / Email notification channel ---
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "ThreatLens AI"
    smtp_use_tls: bool = True

    # --- Auth (shared secret with Member 1's JWT implementation) ---
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"

    # --- Internal service-to-service auth for Member 5 -> Member 6 calls ---
    # Used only by the POST /api/v1/alerts/ingest endpoint so the Threat
    # Monitoring module (a backend service, not a logged-in user) can raise
    # alerts without needing a user JWT. Replace with a real service-auth
    # mechanism (mTLS, signed internal JWT, etc.) if the team adopts one.
    alert_ingest_api_key: str = "change-me-internal-key"

    # --- Deduplication window (see service.py for strategy) ---
    alert_dedup_window_minutes: int = 15

    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = AlertSettings()
