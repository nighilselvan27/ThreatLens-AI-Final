"""
Notification dispatch for alerts.

Implements the "Email/SMTP Service" external integration shown in the
architecture diagram's Alert Service block. Falls back to a console
notifier when SMTP isn't configured (e.g. local dev) or when
NOTIFICATIONS_ENABLED=false, so the module never crashes for lack of mail
server credentials.

INTEGRATION NOTE: If the team later adds other channels (Slack, SIEM/SOAR
webhook — shown as an external integration in the architecture diagram),
add a new `send_via_x()` function here and register it in
`NOTIFICATION_CHANNELS` rather than branching inside `notify()`.
"""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger("member6.notifier")


class NotificationError(Exception):
    """Raised when a notification could not be delivered."""


def _send_console(recipient_role: str, subject: str, body: str) -> str:
    logger.info("[CONSOLE ALERT] to=%s subject=%s\n%s", recipient_role, subject, body)
    return "console"


def _send_email(recipient_email: str, subject: str, body: str) -> str:
    if not settings.smtp_host:
        raise NotificationError("SMTP_HOST is not configured")

    msg = EmailMessage()
    msg["From"] = settings.alert_from_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:
        raise NotificationError(f"Failed to send email: {exc}") from exc

    return "email"


def notify(recipient_role: str, subject: str, body: str, recipient_email: str | None = None) -> str:
    """Dispatch a notification. Returns the channel actually used.

    Never raises for "no SMTP configured" — degrades to console logging so
    alert creation itself never fails due to notification delivery issues.
    Real delivery failures (bad SMTP creds mid-connection, etc.) are caught
    and logged, also degrading to console rather than raising, so a
    downstream email outage can't block alert generation.
    """
    if not settings.notifications_enabled:
        return _send_console(recipient_role, subject, body)

    if recipient_email and settings.smtp_host:
        try:
            return _send_email(recipient_email, subject, body)
        except NotificationError as exc:
            logger.warning("Email delivery failed, falling back to console: %s", exc)
            return _send_console(recipient_role, subject, body)

    return _send_console(recipient_role, subject, body)
