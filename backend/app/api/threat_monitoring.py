"""
REST API endpoints for the Threat Monitoring module.

Base path: /api/v1/threats

Provides endpoints for:
    - Recording new detections (after AI prediction)
    - Querying threat history (filtered, paginated)
    - Viewing threat details with timeline
    - Updating threat status
    - Tracking malware by file hash
    - Dashboard summary statistics
    - Detection trends (time-series)
    - Malware family breakdown
    - Report generation
    - MongoDB detection logs

RBAC:
    All authenticated roles can view threats.
    Security Analysts and Admins can create/update/resolve.
    Only Admins can delete.
"""

import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.modules.threat_monitoring.service import ThreatMonitoringService
from app.modules.threat_monitoring.mongo_repository import MongoThreatLogger
from app.modules.threat_monitoring.schemas import (
    ThreatLogCreate,
    ThreatLogResponse,
    ThreatLogUpdate,
    ThreatStatusUpdate,
    ThreatSummaryResponse,
    ThreatTrendResponse,
    MalwareFamilyBreakdownResponse,
    ThreatReportResponse,
    PaginatedThreatResponse,
    MongoDetectionLogResponse,
    MongoLogsListResponse,
    ThreatTimelineEventResponse,
)

logger = logging.getLogger("threat_monitoring.api")

router = APIRouter(
    prefix="/api/v1/threats",
    tags=["Threat Monitoring"],
)


# ---------------------------------------------------------------------------
# Auth helpers — try to use the existing middleware, fall back to no-auth
# ---------------------------------------------------------------------------

def _get_current_user_optional():
    """
    Try to import the auth middleware. If it fails (e.g. database not configured),
    return a stub dependency that always returns None.
    """
    try:
        from app.middleware.auth_middleware import get_current_user
        return get_current_user
    except Exception:
        async def _no_auth():
            return None
        return _no_auth


def _get_role_checker(allowed_roles: list):
    """
    Try to import the RoleChecker. If it fails, return a pass-through dependency.
    """
    try:
        from app.middleware.auth_middleware import RoleChecker
        return Depends(RoleChecker(allowed_roles))
    except Exception:
        return Depends(lambda: None)


# ---------------------------------------------------------------------------
# DETECTION — Record a new detection
# ---------------------------------------------------------------------------

@router.post(
    "/detect",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Record a new malware detection",
    description="Records the result of an AI prediction. Calculates risk score, "
                "saves to PostgreSQL and MongoDB, creates timeline event, "
                "and triggers an alert if malware is detected.",
)
def record_detection(
    payload: ThreatLogCreate,
    db: Session = Depends(get_db),
):
    """Record a new detection event from the AI prediction engine."""
    try:
        result = ThreatMonitoringService.record_detection(db, payload)
        return result
    except Exception as e:
        logger.error("Failed to record detection: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record detection: {str(e)}",
        )


@router.post(
    "/detect/internal",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Record detection (service-to-service)",
    description="Internal endpoint for service-to-service detection recording. "
                "Accepts an API key instead of user JWT.",
)
def record_detection_internal(
    payload: ThreatLogCreate,
    db: Session = Depends(get_db),
    x_internal_api_key: Optional[str] = Header(default=None),
):
    """
    Service-to-service detection recording endpoint.
    Used by the AI prediction module or external scanners to push detections.
    """
    # Simple API key validation (matches the alert module's pattern)
    import os
    expected_key = os.getenv("ALERT_INGEST_API_KEY", "change-me-internal-key")
    if x_internal_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing internal API key",
        )

    try:
        result = ThreatMonitoringService.record_detection(db, payload)
        return result
    except Exception as e:
        logger.error("Failed to record detection (internal): %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record detection: {str(e)}",
        )


# ---------------------------------------------------------------------------
# QUERY — List threats (paginated, filtered)
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=PaginatedThreatResponse,
    summary="List all threats",
    description="Returns a paginated, filtered list of all threat detections.",
)
def list_threats(
    prediction: Optional[str] = Query(None, description="Filter by malware family"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    threat_status: Optional[str] = Query(None, alias="status", description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by filename or hash"),
    date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[str] = Query(None, description="End date (ISO format)"),
    sort_by: str = Query("detected_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Get paginated threat history with optional filters."""
    # Parse dates if provided
    parsed_from = None
    parsed_to = None
    if date_from:
        try:
            parsed_from = datetime.fromisoformat(date_from)
        except ValueError:
            raise HTTPException(400, detail="Invalid date_from format. Use ISO format.")
    if date_to:
        try:
            parsed_to = datetime.fromisoformat(date_to)
        except ValueError:
            raise HTTPException(400, detail="Invalid date_to format. Use ISO format.")

    return ThreatMonitoringService.get_threat_history(
        db,
        prediction=prediction,
        risk_level=risk_level,
        status=threat_status,
        search=search,
        date_from=parsed_from,
        date_to=parsed_to,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )


# ---------------------------------------------------------------------------
# MALWARE TRACKING
# ---------------------------------------------------------------------------

@router.get(
    "/track/{file_hash}",
    response_model=List[ThreatLogResponse],
    summary="Track file across detections",
    description="Find all detections of the same file by its SHA-256 hash.",
)
def track_malware(
    file_hash: str,
    db: Session = Depends(get_db),
):
    """Track a file across all detection events using its hash."""
    results = ThreatMonitoringService.track_malware(db, file_hash)
    return results


# ---------------------------------------------------------------------------
# TIMELINE
# ---------------------------------------------------------------------------

@router.get(
    "/timeline/{threat_id}",
    response_model=list,
    summary="Get threat timeline",
    description="Returns the chronological timeline of events for a specific threat.",
)
def get_threat_timeline(
    threat_id: str,
    db: Session = Depends(get_db),
):
    """Get the event timeline for a specific threat."""
    timeline = ThreatMonitoringService.get_threat_timeline(db, threat_id)
    if timeline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Threat not found",
        )
    return timeline


# ---------------------------------------------------------------------------
# DASHBOARD ENDPOINTS
# ---------------------------------------------------------------------------

@router.get(
    "/dashboard/summary",
    response_model=ThreatSummaryResponse,
    summary="Dashboard summary statistics",
    description="Returns aggregated statistics for the monitoring dashboard.",
)
def dashboard_summary(
    db: Session = Depends(get_db),
):
    """Get dashboard summary statistics."""
    return ThreatMonitoringService.get_dashboard_summary(db)


@router.get(
    "/dashboard/trends",
    response_model=ThreatTrendResponse,
    summary="Detection trends",
    description="Returns daily detection counts for charts (time-series data).",
)
def dashboard_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    db: Session = Depends(get_db),
):
    """Get detection trend data for the last N days."""
    return ThreatMonitoringService.get_detection_trends(db, days)


@router.get(
    "/dashboard/families",
    response_model=MalwareFamilyBreakdownResponse,
    summary="Malware family breakdown",
    description="Returns malware detection counts grouped by family (pie chart data).",
)
def dashboard_families(
    limit: int = Query(10, ge=1, le=50, description="Max number of families"),
    db: Session = Depends(get_db),
):
    """Get malware family distribution data."""
    return ThreatMonitoringService.get_malware_family_breakdown(db, limit)


# ---------------------------------------------------------------------------
# REPORTS
# ---------------------------------------------------------------------------

@router.get(
    "/reports/generate",
    response_model=ThreatReportResponse,
    summary="Generate threat report",
    description="Generates a comprehensive threat report combining summary, trends, "
                "family breakdown, critical threats, and status distribution.",
)
def generate_report(
    days: int = Query(30, ge=1, le=365, description="Report time window (days)"),
    db: Session = Depends(get_db),
):
    """Generate a comprehensive threat monitoring report."""
    return ThreatMonitoringService.generate_threat_report(db, days)


# ---------------------------------------------------------------------------
# MONGODB LOGS
# ---------------------------------------------------------------------------

@router.get(
    "/logs",
    response_model=MongoLogsListResponse,
    summary="List MongoDB detection logs",
    description="Returns paginated detection audit logs from MongoDB.",
)
def list_detection_logs(
    prediction: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    filename: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Query MongoDB detection audit logs."""
    items, total = MongoThreatLogger.get_logs(
        prediction=prediction,
        risk_level=risk_level,
        filename=filename,
        limit=limit,
        offset=offset,
    )

    return MongoLogsListResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[
            MongoDetectionLogResponse(
                id=item.get("id", ""),
                threat_id=item.get("threat_id"),
                filename=item.get("filename", ""),
                prediction=item.get("prediction", ""),
                confidence=item.get("confidence", 0),
                risk_score=item.get("risk_score", 0),
                risk_level=item.get("risk_level", ""),
                detection_engine=item.get("detection_engine"),
                raw_payload=item.get("raw_payload"),
                logged_at=item.get("logged_at"),
            )
            for item in items
        ],
    )


@router.get(
    "/logs/{log_id}",
    response_model=dict,
    summary="Get single MongoDB detection log",
    description="Returns a single detection audit log entry from MongoDB.",
)
def get_detection_log(log_id: str):
    """Retrieve a single MongoDB detection log by ID."""
    log = MongoThreatLogger.get_log_by_id(log_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection log not found (MongoDB may be unavailable)",
        )
    return log


# ---------------------------------------------------------------------------
# QUERY — Single threat detail
# ---------------------------------------------------------------------------

@router.get(
    "/{threat_id}",
    response_model=ThreatLogResponse,
    summary="Get threat details",
    description="Returns full threat details including timeline events.",
)
def get_threat(
    threat_id: str,
    db: Session = Depends(get_db),
):
    """Get detailed information about a specific threat."""
    threat = ThreatMonitoringService.get_threat_detail(db, threat_id)
    if not threat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Threat not found",
        )
    return threat


# ---------------------------------------------------------------------------
# STATUS UPDATES
# ---------------------------------------------------------------------------

@router.patch(
    "/{threat_id}/status",
    response_model=ThreatLogResponse,
    summary="Update threat status",
    description="Update the status of a threat (e.g., to 'under_investigation', 'confirmed', 'resolved').",
)
def update_threat_status(
    threat_id: str,
    payload: ThreatStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update a threat's status and log the change on the timeline."""
    result = ThreatMonitoringService.update_threat_status(
        db,
        threat_id,
        new_status=payload.status.value,
        updated_by="api_user",
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Threat not found or invalid status",
        )
    return result


@router.patch(
    "/{threat_id}/resolve",
    response_model=ThreatLogResponse,
    summary="Resolve a threat",
    description="Mark a threat as resolved.",
)
def resolve_threat(
    threat_id: str,
    db: Session = Depends(get_db),
):
    """Mark a threat as resolved and log the resolution event."""
    result = ThreatMonitoringService.resolve_threat(
        db,
        threat_id,
        resolved_by="api_user",
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Threat not found",
        )
    return result


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------

@router.delete(
    "/{threat_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a threat",
    description="Permanently delete a threat and all associated data. Admin only.",
)
def delete_threat(
    threat_id: str,
    db: Session = Depends(get_db),
):
    """Delete a threat record. Requires admin role."""
    deleted = ThreatMonitoringService.delete_threat(db, threat_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Threat not found",
        )
    return None

