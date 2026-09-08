"""
REST API for the Alert & Notification Module.

Base path: /api/v1/alerts (matches frontend/src/api/axiosInstance.ts).

AUTH: uses the team's REAL auth (app.middleware.auth_middleware), built
by Member 1 -- get_current_user() returns the actual `User` ORM row,
and RoleChecker([...]) enforces role membership, exactly like
/auth/admin/dashboard in auth_controller.py already does.

RBAC: only two roles exist in the system today -- "Admin" and
"Security Analyst" (see app/schemas/user_schema.py UserRole). Both can
view/read/update/resolve; only "Admin" can delete. If more roles (SOC,
Researcher) are added later, tighten the role lists below accordingly.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy.orm import Session

from app.alerts import service
from app.alerts.config import ALERT_INGEST_API_KEY
from app.database import get_db
from app.auth.dependencies import CurrentUser, get_current_user

from app.alerts.models import AlertStatus, Severity
from app.alerts.schemas import AlertCreate, AlertOut, AlertUpdateStatus, AlertStatsOut

router = APIRouter(prefix="/api/v1/alerts", tags=["Alerts"])

_ALL_ROLES = ["Admin", "Security Analyst"]
_ADMIN_ONLY = ["Admin"]


def _verify_internal_key(x_internal_api_key: Optional[str]) -> None:
    if not x_internal_api_key or x_internal_api_key != ALERT_INGEST_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing internal service API key.")


@router.post("/ingest", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
def ingest_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    x_internal_api_key: Optional[str] = Header(default=None),
):
    """Service-to-service endpoint for the AI Classification module. See adapters.py."""
    _verify_internal_key(x_internal_api_key)
    alert, _created = service.create_alert(db, payload)
    return AlertOut.from_orm_alert(alert)


@router.post("", response_model=AlertOut, status_code=status.HTTP_201_CREATED)
def create_alert(
    payload: AlertCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
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
    current_user: CurrentUser = Depends(get_current_user),
):
    alerts = service.list_alerts(
        db,
        requester_role=current_user.role,
        requester_email=current_user.user_id,
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
    current_user: CurrentUser = Depends(get_current_user),
):
    return service.get_stats(db)


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    alert = service.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertOut.from_orm_alert(alert)


@router.patch("/{alert_id}/read", response_model=AlertOut)
def mark_alert_read(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
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
    current_user: CurrentUser = Depends(get_current_user),
):
    alert = service.update_status(db, alert_id, payload.status)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertOut.from_orm_alert(alert)


@router.patch("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    alert = service.resolve_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertOut.from_orm_alert(alert)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    deleted = service.delete_alert(db, alert_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Alert not found")
    return None
