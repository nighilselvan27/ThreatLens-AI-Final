"""
Core business logic for creating, querying, and updating alerts.

Deduplication strategy (PDF spec section 11):
  1. Exact match: if `source_reference_id` is provided (a stable id for
     the detection/scan event), and an alert with the same
     (source_reference_id, alert_type) already exists, return that
     existing alert instead of creating a new one. This is the primary
     path once Member 5's module produces a real detection/scan id.
  2. Fallback fingerprint: Member 5's current (incomplete) module has no
     stable event id at all -- see adapters.py -- so as a fallback, an
     alert is also considered a duplicate if one with the same
     (file_hash_sha256, alert_type) was created within the last
     `ALERT_DEDUP_WINDOW_MINUTES` (default 15). This prevents a single
     file being rescanned/reclassified repeatedly from spamming
     identical alerts, while still allowing a *new* alert if the same
     file resurfaces later (e.g. re-detected after being marked resolved).
Both are documented assumptions since neither the PDF nor the repo
defines a canonical event id or dedup window.
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.alerts.config import settings
from app.alerts.models import Alert, AlertStatus, Severity
from app.alerts.schemas import AlertCreate
from app.alerts.notifier import dispatch


def _find_duplicate(db: Session, payload: AlertCreate) -> Optional[Alert]:
    if payload.source_reference_id:
        existing = (
            db.query(Alert)
            .filter(
                Alert.source_reference_id == payload.source_reference_id,
                Alert.alert_type == payload.alert_type,
            )
            .first()
        )
        if existing:
            return existing

    if payload.file_hash_sha256:
        window_start = datetime.utcnow() - timedelta(minutes=settings.alert_dedup_window_minutes)
        existing = (
            db.query(Alert)
            .filter(
                Alert.file_hash_sha256 == payload.file_hash_sha256,
                Alert.alert_type == payload.alert_type,
                Alert.created_at >= window_start,
            )
            .order_by(Alert.created_at.desc())
            .first()
        )
        if existing:
            return existing

    return None


def create_alert(db: Session, payload: AlertCreate) -> tuple[Alert, bool]:
    """
    Creates a new alert, or returns the existing duplicate if one was
    found. Returns (alert, was_created) so callers/tests can tell the
    two cases apart.
    """
    duplicate = _find_duplicate(db, payload)
    if duplicate is not None:
        return duplicate, False

    alert = Alert(
        source_reference_id=payload.source_reference_id,
        file_name=payload.file_name,
        file_hash_sha256=payload.file_hash_sha256,
        malware_family=payload.malware_family,
        risk_score=payload.risk_score,
        alert_type=payload.alert_type,
        severity=payload.severity,
        title=payload.title,
        message=payload.message,
        source=payload.source,
        status=AlertStatus.DETECTED,
        recipient_user_id=payload.recipient_user_id,
        recipient_email=payload.recipient_email,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    results = dispatch(alert)
    if results.get("email"):
        alert.email_sent = True
        alert.email_sent_at = datetime.utcnow()
        db.commit()
        db.refresh(alert)

    return alert, True


def list_alerts(
    db: Session,
    *,
    requester_role: str,
    requester_user_id: str,
    status: Optional[AlertStatus] = None,
    severity: Optional[Severity] = None,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
):
    query = db.query(Alert)

    # RBAC scoping (documented assumption -- see auth_stub.py / README):
    # analysts, SOC members, and administrators get org-wide visibility
    # (matches the PDF's SOC/analyst dashboards, which monitor all active
    # threats). Researchers only see alerts addressed to them.
    if requester_role == "researcher":
        query = query.filter(Alert.recipient_user_id == requester_user_id)

    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    if unread_only:
        query = query.filter(Alert.is_read.is_(False))

    return query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()


def get_alert(db: Session, alert_id) -> Optional[Alert]:
    return db.query(Alert).filter(Alert.id == alert_id).first()


def mark_as_read(db: Session, alert_id) -> Optional[Alert]:
    alert = get_alert(db, alert_id)
    if not alert:
        return None
    alert.is_read = True
    db.commit()
    db.refresh(alert)
    return alert


def update_status(db: Session, alert_id, new_status: AlertStatus) -> Optional[Alert]:
    alert = get_alert(db, alert_id)
    if not alert:
        return None
    alert.status = new_status
    if new_status in (AlertStatus.RESOLVED, AlertStatus.FALSE_POSITIVE):
        alert.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert


def resolve_alert(db: Session, alert_id) -> Optional[Alert]:
    return update_status(db, alert_id, AlertStatus.RESOLVED)


def delete_alert(db: Session, alert_id) -> bool:
    alert = get_alert(db, alert_id)
    if not alert:
        return False
    db.delete(alert)
    db.commit()
    return True


def get_stats(db: Session, *, requester_role: str, requester_user_id: str) -> dict:
    query = db.query(Alert)
    if requester_role == "researcher":
        query = query.filter(Alert.recipient_user_id == requester_user_id)

    alerts = query.all()
    total = len(alerts)
    unread = sum(1 for a in alerts if not a.is_read)
    critical = sum(1 for a in alerts if a.severity == Severity.CRITICAL)
    resolved = sum(1 for a in alerts if a.status in (AlertStatus.RESOLVED, AlertStatus.FALSE_POSITIVE))
    active = total - resolved

    by_severity = {s.value: sum(1 for a in alerts if a.severity == s) for s in Severity}
    by_status = {s.value: sum(1 for a in alerts if a.status == s) for s in AlertStatus}

    return {
        "total": total,
        "unread": unread,
        "critical": critical,
        "active": active,
        "resolved": resolved,
        "by_severity": by_severity,
        "by_status": by_status,
    }
