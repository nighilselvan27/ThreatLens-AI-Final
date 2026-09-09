"""
Bridge between the Threat Monitoring module and the Alert & Notification module.

When a malware detection is recorded, this module translates the detection
event into an alert payload and calls the alert service to create the alert.

This implements "Option A" from the adapters.py design doc — same-process,
direct function call, no HTTP round-trip.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.modules.threat_monitoring.models import ThreatLog

logger = logging.getLogger("threat_monitoring.alert_integration")


# Severity mapping: risk_level → alert severity
_RISK_TO_SEVERITY = {
    "critical": "critical",
    "high": "high",
    "medium": "medium",
    "low": "low",
    "minimal": "info",
}


def trigger_alert_for_detection(
    db: Session,
    threat: ThreatLog,
    risk_level: str,
    recipient_user_id: Optional[str] = None,
    recipient_email: Optional[str] = None,
) -> Optional[dict]:
    """
    Create a security alert for a malware detection.

    Attempts to use the existing Alert & Notification module (Member 6's code).
    If the alert module is not available or import fails, logs a warning and
    returns None — the detection is still recorded, just without an alert.

    Args:
        db: SQLAlchemy session (may be the threat monitoring session).
        threat: The saved ThreatLog ORM instance.
        risk_level: Calculated risk level string.
        recipient_user_id: Optional target user for the alert.
        recipient_email: Optional target email for notification.

    Returns:
        Alert creation result dict, or None if alert creation was skipped.
    """

    try:
        # Try to import the alert adapter (from root-level adapters.py)
        from adapters import build_alert_from_threat_event, is_benign

        # Build the detection result dict in the format the adapter expects
        detection_result = {
            "message": f"Malware detected: {threat.prediction}",
            "filename": threat.filename,
            "prediction": threat.prediction,
            "confidence": threat.confidence,
            "risk_score": threat.risk_score,
            "risk_level": _risk_level_to_label(risk_level),
            "file_hash": threat.file_hash_sha256,
            "detection_id": threat.id,
        }

        if is_benign(detection_result["prediction"]):
            logger.debug("Skipping alert for benign detection: %s", threat.filename)
            return None

        alert_payload = build_alert_from_threat_event(
            detection_result,
            recipient_user_id=recipient_user_id,
            recipient_email=recipient_email,
        )

        # Try to create the alert via the service
        try:
            from service import create_alert as alert_service_create
            # Note: the alert module may use its own DB session
            from database import get_db as get_alert_db

            alert_db = next(get_alert_db())
            try:
                alert, created = alert_service_create(alert_db, alert_payload)
                logger.info(
                    "Alert %s for detection %s (created=%s)",
                    alert.id,
                    threat.id,
                    created,
                )
                return {
                    "alert_id": str(alert.id),
                    "created": created,
                    "severity": str(alert.severity.value) if hasattr(alert.severity, "value") else str(alert.severity),
                }
            finally:
                alert_db.close()

        except ImportError:
            logger.info(
                "Alert service not available. Alert payload built but not persisted. "
                "Detection %s recorded without alert.",
                threat.id,
            )
            return {
                "alert_payload_built": True,
                "persisted": False,
                "reason": "Alert service module not importable",
            }

    except ImportError:
        logger.info(
            "Alert adapter (adapters.py) not importable. "
            "Detection %s recorded without alert integration.",
            threat.id,
        )
        return None

    except Exception as e:
        logger.warning(
            "Alert creation failed for detection %s: %s. "
            "Detection was still recorded successfully.",
            threat.id,
            str(e),
        )
        return None


def _risk_level_to_label(risk_level: str) -> str:
    """
    Convert risk level enum value to the human-readable label
    expected by the alert adapter.

    'critical' → 'High Risk'  (adapter maps this to CRITICAL severity)
    'high'     → 'Medium Risk'
    'medium'   → 'Low Risk'
    'low'      → 'Minimal Risk'
    'minimal'  → 'Minimal Risk'
    """
    mapping = {
        "critical": "High Risk",
        "high": "Medium Risk",
        "medium": "Low Risk",
        "low": "Minimal Risk",
        "minimal": "Minimal Risk",
    }
    return mapping.get(risk_level, "Low Risk")
