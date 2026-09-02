from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.alert import AlertSeverity, AlertStatus


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    detection_id: str
    file_id: Optional[str]
    malware_family: Optional[str]
    risk_score: float
    confidence_score: Optional[float]
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: str
    recipient_role: str
    notified: bool
    notification_channel: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]


class AlertStatusUpdate(BaseModel):
    status: AlertStatus


class AlertListFilters(BaseModel):
    status: Optional[AlertStatus] = None
    severity: Optional[AlertSeverity] = None
    recipient_role: Optional[str] = None
