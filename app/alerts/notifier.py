"""Notification dispatch. The Alert row itself is the in-app notification."""

import logging
from abc import ABC, abstractmethod

from app.alerts.models import Alert
from app.alerts.email_service import send_alert_email

logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    name: str

    @abstractmethod
    def send(self, alert: Alert) -> bool:
        raise NotImplementedError


class EmailNotificationChannel(NotificationChannel):
    name = "email"

    def send(self, alert: Alert) -> bool:
        try:
            return send_alert_email(alert)
        except Exception as exc:  # noqa: BLE001
            logger.error("Email channel failed for alert_id=%s: %s", alert.id, exc)
            return False


CHANNELS: list[NotificationChannel] = [EmailNotificationChannel()]


def dispatch(alert: Alert) -> dict:
    return {channel.name: channel.send(alert) for channel in CHANNELS}
