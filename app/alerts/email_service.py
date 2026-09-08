"""Outbound email notifications via SMTP, rendering the alert_email.html template."""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.alerts import config
from app.alerts.models import Alert

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
_env = Environment(loader=FileSystemLoader(_TEMPLATES_DIR), autoescape=select_autoescape(["html"]))


def render_alert_email(alert: Alert) -> str:
    return _env.get_template("alert_email.html").render(alert=alert)


def send_alert_email(alert: Alert) -> bool:
    if not alert.recipient_user_email:
        logger.info("Alert %s has no recipient email; skipping.", alert.id)
        return False

    subject = f"[{alert.severity.value.upper()}] ThreatLens Alert: {alert.title}"
    html_body = render_alert_email(alert)

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{config.SMTP_FROM_NAME} <{config.SMTP_USERNAME}>"
    message["To"] = alert.recipient_user_email
    message.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            if config.SMTP_USE_TLS:
                server.starttls()
            if config.SMTP_USERNAME:
                server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.sendmail(config.SMTP_USERNAME, [alert.recipient_user_email], message.as_string())
        logger.info("Alert email sent for alert_id=%s", alert.id)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to send alert email for alert_id=%s: %s", alert.id, exc)
        return False
