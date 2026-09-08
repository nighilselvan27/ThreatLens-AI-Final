"""
Core business logic: create (with dedup), list (role-scoped), get,
mark-read, status update, resolve, delete, stats.

Deduplication: now that the AI module confirms a stable `detection_id`
on every event, exact-match dedup on (source_reference_id, alert_type)
is the primary and normally-sufficient path. A fallback fingerprint on
(file_id, alert_type, time window) remains for the rare case a caller
omits detection_id.
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.alerts.models import Alert, AlertStatus, Severity
from app.alerts.schemas import AlertCreate
from app.alerts.notifier import dispatch

ALERT_DEDUP_WINDOW_MINUTES = 15  # fallback path only; see docstring above


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

    if payload.file_id:
        window_start = datetime.utcnow() - timedelta(minutes=ALERT_DEDUP_WINDOW_MINUTES)
        existing = (
            db.query(Alert)
            .filter(
                Alert.file_id == payload.file_id,
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
    duplicate = _find_duplicate(db, payload)
    if duplicate is not None:
        return duplicate, False

    alert = Alert(
        source_reference_id=payload.source_reference_id,
        file_id=payload.file_id,
        file_name=payload.file_name,
        file_hash_sha256=payload.file_hash_sha256,
        malware_family=payload.malware_family,
        risk_score=payload.risk_score,
        malware_probability=payload.malware_probability,
        alert_type=payload.alert_type,
        severity=payload.severity,
        title=payload.title,
        message=payload.message,
        source=payload.source,
        status=AlertStatus.DETECTED,
        recipient_user_email=payload.recipient_user_email,
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
    requester_email: str,
    status: Optional[AlertStatus] = None,
    severity: Optional[Severity] = None,
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
):
    query = db.query(Alert)

    # RBAC scoping: only two roles exist today (Admin, Security Analyst),
    # and both get org-wide visibility per the PDF's SOC/analyst dashboard
    # requirements. If/when a more restricted role (e.g. Researcher) is
    # added, scope it here the same way this used to scope "researcher".
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


def get_stats(db: Session) -> dict:
    alerts = db.query(Alert).all()
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
