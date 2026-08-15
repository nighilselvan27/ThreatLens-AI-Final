"""
Pydantic request/response schemas for the Alert & Notification Module.

Naming convention: request/internal schemas use snake_case (Python/PEP 8
convention, matches the rest of the backend). The response schema
(`AlertOut`) uses camelCase attribute names deliberately, because it is
serialized directly for Member 7's frontend, which expects:

    { id, title, message, severity, isRead, createdAt, source }

(see frontend/src/types/alert.types.ts). Extra fields beyond that shape
are additive and safe -- the frontend simply ignores keys it doesn't
declare in its TypeScript interface.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict, Field

from app.alerts.models import Severity, AlertStatus, AlertType


class AlertCreate(BaseModel):
    """
    Payload for raising a new alert. Used both by the internal
    /ingest endpoint (called by/on behalf of Member 5) and by the
    authenticated POST /api/v1/alerts endpoint (manual creation by
    a Security Analyst or Administrator).
    """

    source_reference_id: Optional[str] = None
    file_name: Optional[str] = None
    file_hash_sha256: Optional[str] = None
    malware_family: Optional[str] = None
    risk_score: Optional[float] = Field(default=None, ge=0, le=100)

    alert_type: AlertType = AlertType.MALWARE_DETECTED
    severity: Severity = Severity.MEDIUM

    title: str
    message: str
    source: str = "Threat Monitoring"

    recipient_user_id: Optional[str] = None
    recipient_email: Optional[EmailStr] = None


class AlertUpdateStatus(BaseModel):
    status: AlertStatus


class AlertOut(BaseModel):
    """Response shape. Deliberately camelCase -- see module docstring."""

    model_config = ConfigDict(populate_by_name=True)

    id: uuid.UUID
    title: str
    message: str
    severity: Severity
    isRead: bool
    createdAt: datetime
    source: str

    # Additional fields beyond the frontend's minimal contract:
    status: AlertStatus
    alertType: AlertType
    riskScore: Optional[float]
    malwareFamily: Optional[str]
    fileName: Optional[str]
    fileHashSha256: Optional[str]
    sourceReferenceId: Optional[str]
    recipientUserId: Optional[str]
    updatedAt: Optional[datetime]
    resolvedAt: Optional[datetime]

    @classmethod
    def from_orm_alert(cls, alert) -> "AlertOut":
        return cls(
            id=alert.id,
            title=alert.title,
            message=alert.message,
            severity=alert.severity,
            isRead=alert.is_read,
            createdAt=alert.created_at,
            source=alert.source,
            status=alert.status,
            alertType=alert.alert_type,
            riskScore=alert.risk_score,
            malwareFamily=alert.malware_family,
            fileName=alert.file_name,
            fileHashSha256=alert.file_hash_sha256,
            sourceReferenceId=alert.source_reference_id,
            recipientUserId=alert.recipient_user_id,
            updatedAt=alert.updated_at,
            resolvedAt=alert.resolved_at,
        )


class AlertStatsOut(BaseModel):
    total: int
    unread: int
    critical: int
    active: int  # not resolved and not false_positive
    resolved: int
    by_severity: dict
    by_status: dict
