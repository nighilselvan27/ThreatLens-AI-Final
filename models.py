"""
Database models for the Alert & Notification Module.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Enum, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Severity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Alert(Base):
    """
    An alert generated from a confirmed malware detection.
    Created by the Threat Monitoring module (Member 5) via the AI
    prediction pipeline, then processed and delivered by this module.
    """

    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Link back to the detection / file scan that triggered this alert
    detection_id = Column(String(255), nullable=False, index=True)
    file_name = Column(String(500), nullable=True)
    file_hash_sha256 = Column(String(64), nullable=True, index=True)

    threat_type = Column(String(255), nullable=True)  # e.g. "Trojan", "Ransomware"
    severity = Column(Enum(Severity), nullable=False, default=Severity.MEDIUM)
    risk_score = Column(String(10), nullable=True)  # e.g. "87.5"

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    status = Column(Enum(AlertStatus), nullable=False, default=AlertStatus.NEW)

    # Recipient of the notification (user id from Member 1's User module)
    recipient_user_id = Column(String(255), nullable=True, index=True)
    recipient_email = Column(String(255), nullable=True)

    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
