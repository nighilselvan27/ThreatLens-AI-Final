"""
Database model for the Alert & Notification Module.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Enum,
    Text,
    Boolean,
    Float,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID

from app.alerts.database import Base


class Severity(str, enum.Enum):
    """
    Alert severity levels.

    ASSUMPTION: The PDF spec (section 6) lists LOW/MEDIUM/HIGH/CRITICAL as
    an example only and says to check the repo for an existing convention
    first. Member 7's frontend (frontend/src/types/threat.types.ts) already
    defines and *renders* a 5-level Severity type:

        "critical" | "high" | "medium" | "low" | "info"

    This model adopts that exact convention (values match the frontend's
    string literals) so the API response requires zero frontend changes.
    INFO is reserved for non-detection informational alerts (e.g. "YARA
    rule updated") — the Member 5 adapter never emits INFO on its own.
    """

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, enum.Enum):
    """
    Detection/investigation status, per PDF spec section 4C:
    Detected -> Under Investigation -> Confirmed -> Resolved (or False Positive).
    """

    DETECTED = "detected"
    UNDER_INVESTIGATION = "under_investigation"
    CONFIRMED = "confirmed"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class AlertType(str, enum.Enum):
    """
    Coarse alert category, per PDF spec sections 4A/4B examples.
    Kept as an enum (rather than a free-text field) so the frontend can
    filter/group reliably; extend this list as new detection scenarios
    are added, rather than inventing ad-hoc strings elsewhere.
    """

    MALWARE_DETECTED = "malware_detected"
    HIGH_RISK_FILE = "high_risk_file"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    THREAT_ESCALATION = "threat_escalation"
    NEW_THREAT = "new_threat"
    INVESTIGATION_REQUIRED = "investigation_required"
    SECURITY_WARNING = "security_warning"
    SYSTEM_NOTICE = "system_notice"


class Alert(Base):
    """
    An alert raised from a confirmed/suspected detection.

    Field naming note: several columns are exposed to the frontend under
    camelCase names via schemas.py (AlertOut). The DB columns themselves
    stay snake_case (normal SQLAlchemy/PEP 8 convention); only the API
    response layer translates naming, so this stays consistent with the
    rest of the Python codebase.
    """

    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # --- Link back to the detection/scan/threat event that triggered this ---
    # Member 5's detection payload has no stable natural key today (see
    # adapters.py), so this is nullable. When Member 5 adds a proper
    # detection/scan id, populate this for exact-match deduplication.
    source_reference_id = Column(String(255), nullable=True, index=True)
    file_name = Column(String(500), nullable=True)
    file_hash_sha256 = Column(String(64), nullable=True, index=True)
    malware_family = Column(String(255), nullable=True)  # e.g. "Trojan", "Ransomware"
    risk_score = Column(Float, nullable=True)  # 0-100, from Member 5 / classification module

    alert_type = Column(Enum(AlertType), nullable=False, default=AlertType.MALWARE_DETECTED)
    severity = Column(Enum(Severity), nullable=False, default=Severity.MEDIUM)

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    source = Column(String(255), nullable=False, default="Threat Monitoring")

    status = Column(Enum(AlertStatus), nullable=False, default=AlertStatus.DETECTED)

    # Recipient of the notification (user id from Member 1's User module).
    # Nullable: alerts with no recipient are treated as broadcast/role-wide
    # (e.g. visible to all Security Analysts) rather than addressed to one user.
    recipient_user_id = Column(String(255), nullable=True, index=True)
    recipient_email = Column(String(255), nullable=True)

    is_read = Column(Boolean, nullable=False, default=False)
    email_sent = Column(Boolean, nullable=False, default=False)
    email_sent_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    __table_args__ = (
        # Speeds up the common "same detection, same alert type" dedup lookup.
        Index("ix_alerts_dedup_lookup", "source_reference_id", "alert_type"),
        Index("ix_alerts_dedup_fallback", "file_hash_sha256", "alert_type", "created_at"),
    )
