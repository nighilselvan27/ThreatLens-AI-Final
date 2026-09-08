"""
Minimal settings for the Alert & Notification Module.

Everything else this module needs (database, JWT secret, auth) now
comes from the team's real shared modules (app.database.database,
app.middleware.auth_middleware) -- this file only holds the ONE thing
still specific to alerts: the internal service-to-service API key used
by the AI Classification module to call POST /api/v1/alerts/ingest
without needing a full user login.
"""

import os

ALERT_INGEST_API_KEY = os.getenv("ALERT_INGEST_API_KEY", "change-me-internal-key")

# SMTP (email notification channel)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "ThreatLens AI")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
