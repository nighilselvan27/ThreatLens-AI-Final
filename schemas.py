"""
Pydantic schemas used for request validation and API responses.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models import Severity, AlertStatus


class AlertCreate(BaseModel):
    """Payload used by Member 5's Threat Monitoring module to raise a new alert."""

    detection_id: str
    file_name: Optional[str] = None
    file_hash_sha256: Optional[str] = None
    threat_type: Optional[str] = None
    severity: Severity = Severity.MEDIUM
    risk_score: Optional[str] = None
    title: str
    message: str
    recipient_user_id: Optional[str] = None
    recipient_email: Optional[EmailStr] = None


class AlertUpdateStatus(BaseModel):
    status: AlertStatus


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    detection_id: str
    file_name: Optional[str]
    file_hash_sha256: Optional[str]
    threat_type: Optional[str]
    severity: Severity
    risk_score: Optional[str]
    title: str
    message: str
    status: AlertStatus
    recipient_user_id: Optional[str]
    recipient_email: Optional[str]
    email_sent: bool
    email_sent_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
