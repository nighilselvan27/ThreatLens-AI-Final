"""
Outbound email notifications via SMTP, using the JSON-serializable
Alert ORM object to render an HTML template.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.alerts.config import settings
from app.alerts.models import Alert

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
_env = Environment(
    loader=FileSystemLoader(_TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)


def render_alert_email(alert: Alert) -> str:
    template = _env.get_template("alert_email.html")
    return template.render(alert=alert)


def send_alert_email(alert: Alert) -> bool:
    """
    Sends an email notification for the given alert.
    Returns True on success, False on failure -- never raises, so a
    notification failure never blocks alert creation/persistence.
    """
    if not alert.recipient_email:
        logger.info("Alert %s has no recipient email; skipping email send.", alert.id)
        return False

    subject = f"[{alert.severity.value.upper()}] ThreatLens Alert: {alert.title}"
    html_body = render_alert_email(alert)

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_username}>"
    message["To"] = alert.recipient_email
    message.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.sendmail(settings.smtp_username, [alert.recipient_email], message.as_string())
        logger.info("Alert email sent for alert_id=%s", alert.id)
        return True
    except Exception as exc:  # noqa: BLE001 - log and degrade gracefully
        logger.error("Failed to send alert email for alert_id=%s: %s", alert.id, exc)
        return False
