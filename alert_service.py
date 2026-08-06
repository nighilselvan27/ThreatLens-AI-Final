"""
Core business logic for creating and managing alerts.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Alert, AlertStatus
from app.schemas import AlertCreate
from app.services.email_service import send_alert_email


def create_alert(db: Session, payload: AlertCreate) -> Alert:
    """
    Persists a new alert and attempts to notify the recipient by email.
    Called by the Threat Monitoring module once a detection is confirmed.
    """
    alert = Alert(
        detection_id=payload.detection_id,
        file_name=payload.file_name,
        file_hash_sha256=payload.file_hash_sha256,
        threat_type=payload.threat_type,
        severity=payload.severity,
        risk_score=payload.risk_score,
        title=payload.title,
        message=payload.message,
        status=AlertStatus.NEW,
        recipient_user_id=payload.recipient_user_id,
        recipient_email=payload.recipient_email,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    sent = send_alert_email(alert)
    if sent:
        alert.email_sent = True
        alert.email_sent_at = datetime.utcnow()
        db.commit()
        db.refresh(alert)

    return alert


def list_alerts(
    db: Session,
    status: Optional[AlertStatus] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    query = db.query(Alert)
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    return query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()


def get_alert(db: Session, alert_id) -> Optional[Alert]:
    return db.query(Alert).filter(Alert.id == alert_id).first()


def update_alert_status(db: Session, alert_id, status: AlertStatus) -> Optional[Alert]:
    alert = get_alert(db, alert_id)
    if not alert:
        return None
    alert.status = status
    db.commit()
    db.refresh(alert)
    return alert
