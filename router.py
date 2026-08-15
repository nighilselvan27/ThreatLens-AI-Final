"""
REST API for the Alert & Notification Module.

Base path: /api/v1/alerts (matches frontend/src/api/axiosInstance.ts,
which defaults VITE_API_BASE_URL to "/api/v1").

RBAC summary (documented assumption -- see auth_stub.py docstring):
    security_analyst  - view (org-wide), mark read, update status, resolve
    soc_team_member   - view (org-wide), mark read
    administrator     - everything, including delete
    researcher        - view only, scoped to alerts addressed to them
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy.orm import Session

from app.alerts import service
from app.alerts.auth_stub import CurrentUser, get_current_user, require_roles, verify_internal_api_key
from app.alerts.database import get_db
from app.alerts.models import AlertStatus, Severity
from app.alerts.schemas import AlertCreate, AlertOut, AlertUpdateStatus, AlertStatsOut

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])

_ALL_VIEW_ROLES = {"security_analyst", "soc_team_member", "administrator", "researcher"}
_UPDATE_ROLES = {"security_analyst", "administrator"}
_DELETE_ROLES = {"administrator"}
_CREATE_ROLES = {"security_analyst", "administrator"}


@router.post("/ingest", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
def ingest_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    x_internal_api_key: Optional[str] = Header(default=None),
):
    """
    Service-to-service endpoint for Member 5's Threat Monitoring module
    (or anything running as a backend service, not a logged-in user) to
    raise an alert. Requires the X-Internal-Api-Key header instead of a
    user JWT. See adapters.py for how to build the payload from Member
    5's detection result.
    """
    verify_internal_api_key(x_internal_api_key)
    alert, _created = service.create_alert(db, payload)
    return AlertOut.from_orm_alert(alert)


@router.post("", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(_CREATE_ROLES)),
):
    """Manual alert creation by a Security Analyst or Administrator."""
    alert, _created = service.create_alert(db, payload)
    return AlertOut.from_orm_alert(alert)


@router.get("", response_model=List[AlertOut])
def list_alerts(
    status_filter: Optional[AlertStatus] = Query(default=None, alias="status"),
    severity: Optional[Severity] = None,
    unread_only: bool = False,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(_ALL_VIEW_ROLES)),
):
    alerts = service.list_alerts(
        db,
        requester_role=current_user.role,
        requester_user_id=current_user.user_id,
        status=status_filter,
        severity=severity,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    return [AlertOut.from_orm_alert(a) for a in alerts]


@router.get("/stats/summary", response_model=AlertStatsOut)
def alert_stats(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(_ALL_VIEW_ROLES)),
):
    return service.get_stats(db, requester_role=current_user.role, requester_user_id=current_user.user_id)


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(_ALL_VIEW_ROLES)),
):
    alert = service.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if current_user.role == "researcher" and alert.recipient_user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this alert")
    return AlertOut.from_orm_alert(alert)


@router.patch("/{alert_id}/read", response_model=AlertOut)
def mark_alert_read(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(_ALL_VIEW_ROLES)),
):
    alert = service.mark_as_read(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertOut.from_orm_alert(alert)


@router.patch("/{alert_id}/status", response_model=AlertOut)
def update_alert_status(
    alert_id: uuid.UUID,
    payload: AlertUpdateStatus,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(_UPDATE_ROLES)),
):
    alert = service.update_status(db, alert_id, payload.status)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertOut.from_orm_alert(alert)


@router.patch("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(_UPDATE_ROLES)),
):
    alert = service.resolve_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertOut.from_orm_alert(alert)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles(_DELETE_ROLES)),
):
    deleted = service.delete_alert(db, alert_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert not found")
    return None
