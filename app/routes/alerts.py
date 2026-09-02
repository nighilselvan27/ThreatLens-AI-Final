"""
Alert & Notification API routes.

Endpoints:
  POST   /alerts/ingest       - internal: Members 3/5 submit a ThreatDetectionResult
  GET    /alerts/             - list alerts (consumed by Member 7's dashboard)
  GET    /alerts/{alert_id}   - get one alert
  PATCH  /alerts/{alert_id}/status - update alert status (acknowledge/resolve/etc.)
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.models.alert import AlertSeverity, AlertStatus
from app.schemas.alert import AlertRead, AlertStatusUpdate
from app.schemas.integration import ThreatDetectionResult
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/ingest", response_model=AlertRead, status_code=status.HTTP_201_CREATED)
def ingest_detection(
    detection: ThreatDetectionResult,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    """Called by Member 3 (classification) or Member 5 (monitoring) when a
    new threat detection result is produced. Idempotent per detection_id."""
    alert = alert_service.create_alert_from_detection(db, detection)
    return alert


@router.get("/", response_model=list[AlertRead])
def list_alerts(
    status_filter: Optional[AlertStatus] = Query(None, alias="status"),
    severity: Optional[AlertSeverity] = Query(None),
    recipient_role: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    return alert_service.list_alerts(
        db,
        status_filter=status_filter,
        severity_filter=severity,
        recipient_role=recipient_role,
        limit=limit,
        offset=offset,
    )


@router.get("/{alert_id}", response_model=AlertRead)
def get_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    alert = alert_service.get_alert(db, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert


@router.patch("/{alert_id}/status", response_model=AlertRead)
def update_status(
    alert_id: str,
    payload: AlertStatusUpdate,
    db: Session = Depends(get_db),
    _user: CurrentUser = Depends(get_current_user),
):
    alert = alert_service.update_alert_status(db, alert_id, payload.status)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return alert
