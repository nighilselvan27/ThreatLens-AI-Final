"""
Notification dispatch. The Alert row itself IS the in-app notification
(the frontend reads it via GET /api/v1/alerts), so no separate "in-app"
delivery step is required today.

This module exists so Member 8 (or a future sprint) can add more
delivery channels -- WebSocket push, Slack, an external SIEM webhook --
without touching alert_service.py. Add a channel by implementing
`NotificationChannel` and appending an instance to `CHANNELS` below.
"""

import logging
from abc import ABC, abstractmethod

from app.alerts.models import Alert
from app.alerts.email_service import send_alert_email

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    name: str

    @abstractmethod
    def send(self, alert: Alert) -> bool:
        """Attempt delivery. Must never raise -- return False on failure."""
        raise NotImplementedError


class EmailNotificationChannel(NotificationChannel):
    name = "email"

    def send(self, alert: Alert) -> bool:
        try:
            return send_alert_email(alert)
        except Exception as exc:  # noqa: BLE001 - never let a channel crash alert creation
            logger.error("Email channel failed for alert_id=%s: %s", alert.id, exc)
            return False


# Active channels, in order. In-app delivery (the DB row + GET /alerts)
# always happens implicitly and isn't listed here.
CHANNELS: list[NotificationChannel] = [EmailNotificationChannel()]


def dispatch(alert: Alert) -> dict:
    """
    Runs every configured channel for this alert and returns a
    {channel_name: success_bool} summary for logging/telemetry.
    """
    results = {}
    for channel in CHANNELS:
        results[channel.name] = channel.send(alert)
    return results
