"""
Database model for the Alert & Notification Module.

Uses the TEAM'S REAL shared database setup (app.database.database),
built by Member 1 -- no more standalone engine/Base for this module.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Enum, Text, Boolean, Float, Index
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class Severity(str, enum.Enum):
    """
    Alert severity levels. Matches the frontend's Severity type exactly
    (frontend/src/types/threat.types.ts): critical/high/medium/low/info.
    INFO is reserved for non-detection system notices; the AI adapter
    never emits it.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, enum.Enum):
    """Per PDF spec section 4C: Detected -> Under Investigation -> Confirmed -> Resolved/False Positive."""

    DETECTED = "detected"
    UNDER_INVESTIGATION = "under_investigation"
    CONFIRMED = "confirmed"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class AlertType(str, enum.Enum):
    MALWARE_DETECTED = "malware_detected"
    HIGH_RISK_FILE = "high_risk_file"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    THREAT_ESCALATION = "threat_escalation"
    NEW_THREAT = "new_threat"
    INVESTIGATION_REQUIRED = "investigation_required"
    SECURITY_WARNING = "security_warning"
    SYSTEM_NOTICE = "system_notice"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # --- Link back to the AI classification detection that triggered this ---
    # Maps directly to the AI module's `detection_id` -- see adapters.py.
    # This IS the primary key used for exact-match deduplication.
    source_reference_id = Column(String(255), nullable=True, index=True)
    file_id = Column(String(255), nullable=True, index=True)  # AI module's file_id
    file_name = Column(String(500), nullable=True)  # optional, not always available
    file_hash_sha256 = Column(String(64), nullable=True, index=True)  # optional
    malware_family = Column(String(255), nullable=True)
    risk_score = Column(Float, nullable=True)  # 0-100, from the AI/classification module
    malware_probability = Column(Float, nullable=True)  # 0-1, raw model output

    alert_type = Column(Enum(AlertType), nullable=False, default=AlertType.MALWARE_DETECTED)
    severity = Column(Enum(Severity), nullable=False, default=Severity.MEDIUM)

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    source = Column(String(255), nullable=False, default="classification")

    status = Column(Enum(AlertStatus), nullable=False, default=AlertStatus.DETECTED)

    # Recipient -- references app.models.user.User.email (string), since
    # that's the identifier already used across the auth system's JWTs.
    recipient_user_email = Column(String(255), nullable=True, index=True)

    is_read = Column(Boolean, nullable=False, default=False)
    email_sent = Column(Boolean, nullable=False, default=False)
    email_sent_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_alerts_dedup_lookup", "source_reference_id", "alert_type"),
        Index("ix_alerts_dedup_fallback", "file_id", "alert_type", "created_at"),
    )
