"""
Notification APIs — create, list, fetch, and update alerts.
Consumed by the Threat Monitoring module (writer) and the Analytics
Dashboard / frontend (reader).
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AlertStatus
from app.schemas import AlertCreate, AlertOut, AlertUpdateStatus
from app.services import alert_service

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.post("", response_model=AlertOut, status_code=201)
def create_alert(payload: AlertCreate, db: Session = Depends(get_db)):
    """Create a new alert from a confirmed detection and notify the recipient."""
    return alert_service.create_alert(db, payload)


@router.get("", response_model=List[AlertOut])
def list_alerts(
    status: Optional[AlertStatus] = None,
    severity: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List alerts, optionally filtered by status or severity. Used for alert history."""
    return alert_service.list_alerts(db, status=status, severity=severity, limit=limit, offset=offset)


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: uuid.UUID, db: Session = Depends(get_db)):
    alert = alert_service.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/{alert_id}/status", response_model=AlertOut)
def update_alert_status(alert_id: uuid.UUID, payload: AlertUpdateStatus, db: Session = Depends(get_db)):
    """Mark an alert as acknowledged or resolved."""
    alert = alert_service.update_alert_status(db, alert_id, payload.status)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert
