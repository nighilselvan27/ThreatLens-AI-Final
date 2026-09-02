"""
Alert & Notification Module — core service logic.

Owns:
  - Turning a ThreatDetectionResult (from Members 3/5) into an Alert record
  - Deduplicating alerts for the same detection
  - Routing alerts to the right recipient role
  - Triggering notification delivery
  - Status transitions (acknowledge / resolve / dismiss)
  - Listing/filtering alerts for the dashboard (consumed by Member 7)
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.schemas.integration import ThreatDetectionResult
from app.services.notifier import notify


class DuplicateAlertError(Exception):
    """Raised when an alert already exists for this detection_id."""


def _severity_from_risk_score(risk_score: float) -> AlertSeverity:
    """Maps a 0-100 risk score to a severity tier.

    Thresholds follow the PDF's example (risk score 82/100 -> classified
    as a Trojan requiring escalation to a Security Analyst), i.e. high
    scores should reach HIGH/CRITICAL, not just MEDIUM.
    """
    if risk_score >= 90:
        return AlertSeverity.CRITICAL
    if risk_score >= 70:
        return AlertSeverity.HIGH
    if risk_score >= 40:
        return AlertSeverity.MEDIUM
    return AlertSeverity.LOW


def _recipient_role_for_severity(severity: AlertSeverity) -> str:
    """Routes alerts to a role per the PDF's defined roles.

    HIGH/CRITICAL -> security_analyst (per PDF example: "Escalate to
    Security Analyst for Investigation"). Lower severities go to the SOC
    team for routine monitoring.
    """
    if severity in (AlertSeverity.HIGH, AlertSeverity.CRITICAL):
        return "security_analyst"
    return "soc_team"


def _build_message(detection: ThreatDetectionResult, severity: AlertSeverity) -> tuple[str, str]:
    family = detection.malware_family or "Unknown malware"
    title = f"[{severity.value.upper()}] {family} detected (risk {detection.risk_score:.0f}/100)"
    body_lines = [
        f"Detection ID: {detection.detection_id}",
        f"File ID: {detection.file_id or 'N/A'}",
        f"Malware family: {family}",
        f"Risk score: {detection.risk_score:.0f}/100",
    ]
    if detection.confidence_score is not None:
        body_lines.append(f"Confidence: {detection.confidence_score:.2f}")
    body_lines.append(f"Source: {detection.source_module}")
    return title, "\n".join(body_lines)


def create_alert_from_detection(db: Session, detection: ThreatDetectionResult) -> Alert:
    """Create (or return existing) alert for a given detection result.

    Idempotent by detection_id: calling this twice for the same
    detection_id will not create duplicate alerts/notifications, since
    upstream modules may retry or re-publish the same event.
    """
    existing = db.execute(
        select(Alert).where(Alert.detection_id == detection.detection_id)
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    severity = _severity_from_risk_score(detection.risk_score)
    recipient_role = _recipient_role_for_severity(severity)
    title, message = _build_message(detection, severity)

    alert = Alert(
        detection_id=detection.detection_id,
        file_id=detection.file_id,
        malware_family=detection.malware_family,
        risk_score=detection.risk_score,
        confidence_score=detection.confidence_score,
        severity=severity,
        status=AlertStatus.NEW,
        title=title,
        message=message,
        recipient_role=recipient_role,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    channel = notify(recipient_role=recipient_role, subject=title, body=message)
    alert.notified = True
    alert.notification_channel = channel
    db.commit()
    db.refresh(alert)

    return alert


def get_alert(db: Session, alert_id: str) -> Optional[Alert]:
    return db.get(Alert, alert_id)


def list_alerts(
    db: Session,
    status_filter: Optional[AlertStatus] = None,
    severity_filter: Optional[AlertSeverity] = None,
    recipient_role: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Alert]:
    stmt = select(Alert)
    if status_filter is not None:
        stmt = stmt.where(Alert.status == status_filter)
    if severity_filter is not None:
        stmt = stmt.where(Alert.severity == severity_filter)
    if recipient_role is not None:
        stmt = stmt.where(Alert.recipient_role == recipient_role)
    stmt = stmt.order_by(Alert.created_at.desc()).offset(offset).limit(limit)
    return list(db.execute(stmt).scalars().all())


def update_alert_status(db: Session, alert_id: str, new_status: AlertStatus) -> Optional[Alert]:
    from datetime import datetime

    alert = db.get(Alert, alert_id)
    if alert is None:
        return None
    alert.status = new_status
    if new_status in (AlertStatus.RESOLVED, AlertStatus.DISMISSED):
        alert.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert
