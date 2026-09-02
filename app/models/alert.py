"""
Alert model — the single new database table this module owns: `alerts`.

Does not touch or duplicate any table owned by other members (users,
detections, files, etc.). Foreign-key-like fields (detection_id, file_id,
recipient_role) are stored as plain columns rather than real FKs for now,
since the tables they'd reference (owned by Members 1/2/3/5) don't exist
yet in this repo. Once they do, these can be converted to proper
ForeignKey columns — flagged below.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, String, Boolean
from sqlalchemy.orm import Mapped

from app.database import Base


class AlertSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


def _new_id() -> str:
    return str(uuid.uuid4())


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[str] = Column(String(36), primary_key=True, default=_new_id)

    # --- Provenance (from Member 3 classification / Member 5 monitoring) ---
    # TODO(integration): convert to ForeignKey("detections.id") once
    # Member 3/5's detection table exists.
    detection_id = Column(String(64), nullable=False, index=True)
    file_id = Column(String(64), nullable=True, index=True)
    malware_family = Column(String(128), nullable=True)
    risk_score = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=True)

    # --- Alert content ---
    severity = Column(Enum(AlertSeverity), nullable=False, index=True)
    status = Column(Enum(AlertStatus), nullable=False, default=AlertStatus.NEW, index=True)
    title = Column(String(255), nullable=False)
    message = Column(String(2000), nullable=False)

    # --- Routing ---
    # TODO(integration): convert to ForeignKey("users.role") or a real
    # role/user table once Member 1's User Management module exists.
    recipient_role = Column(String(64), nullable=False, index=True)

    # --- Notification tracking ---
    notified = Column(Boolean, default=False, nullable=False)
    notification_channel = Column(String(32), nullable=True)  # e.g. "email", "console"

    # --- Timestamps ---
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Alert id={self.id} severity={self.severity} status={self.status}>"
