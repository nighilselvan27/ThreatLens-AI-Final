"""
SQLAlchemy ORM models for the Threat Monitoring module.

Tables:
    - threat_logs            : Primary detection records (one row per scan result)
    - threat_timeline_events : Chronological events per threat (status changes, analysis steps)

These models live in the same PostgreSQL database as the User and Alert modules
and share the same SQLAlchemy Base.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    Enum,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ThreatStatus(str, enum.Enum):
    """Lifecycle status of a detected threat."""
    DETECTED = "detected"
    QUARANTINED = "quarantined"
    UNDER_INVESTIGATION = "under_investigation"
    CONFIRMED = "confirmed"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    MONITORING = "monitoring"


class RiskLevel(str, enum.Enum):
    """Risk classification derived from the risk score."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class TimelineEventType(str, enum.Enum):
    """Categories of events that appear on a threat's timeline."""
    DETECTED = "detected"
    ANALYZED = "analyzed"
    ESCALATED = "escalated"
    STATUS_CHANGED = "status_changed"
    NOTE_ADDED = "note_added"
    RESOLVED = "resolved"
    REOPENED = "reopened"
    ALERT_CREATED = "alert_created"


# ---------------------------------------------------------------------------
# ThreatLog — Primary detection record
# ---------------------------------------------------------------------------

class ThreatLog(Base):
    """
    Stores the result of every file scan / AI prediction.

    One row is created per detection event. The same physical file
    (identified by SHA-256 hash) may appear in multiple rows if it is
    scanned more than once or detected by different engines.
    """

    __tablename__ = "threat_logs"

    # Primary key — use a string UUID for cross-DB compatibility
    # (SQLite doesn't support native UUID columns).
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # ---- File metadata ----
    filename = Column(String(500), nullable=False, index=True)
    file_hash_md5 = Column(String(32), nullable=True, index=True)
    file_hash_sha256 = Column(String(64), nullable=True, index=True)
    file_size = Column(Integer, nullable=True)           # bytes
    file_type = Column(String(50), nullable=True)        # e.g. "exe", "dll", "pdf"

    # ---- AI prediction results ----
    prediction = Column(String(100), nullable=False, index=True)   # malware family or "Benign"
    confidence = Column(Float, nullable=False, default=0.0)        # 0-100
    detection_engine = Column(String(100), nullable=True, default="ThreatLens AI")

    # ---- Risk assessment ----
    risk_score = Column(Integer, nullable=False, default=0)        # 0-100
    risk_level = Column(
        Enum(RiskLevel, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=RiskLevel.MINIMAL,
        index=True,
    )

    # ---- Status tracking ----
    status = Column(
        Enum(ThreatStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ThreatStatus.DETECTED,
        index=True,
    )

    # ---- Static analysis artifacts ----
    yara_matches = Column(JSON, nullable=True)                     # list of matched rule names
    static_analysis_results = Column(JSON, nullable=True)          # full analysis payload
    suspicious_indicators = Column(JSON, nullable=True)            # URLs, IPs, strings, etc.

    # ---- Description & notes ----
    description = Column(Text, nullable=True)
    recommended_action = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)

    # ---- Ownership ----
    detected_by_user_id = Column(Integer, nullable=True)           # FK conceptual to users.id

    # ---- Timestamps ----
    detected_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # ---- Relationships ----
    timeline_events = relationship(
        "ThreatTimelineEvent",
        back_populates="threat",
        cascade="all, delete-orphan",
        order_by="ThreatTimelineEvent.created_at",
    )

    __table_args__ = (
        Index("ix_threat_logs_hash_prediction", "file_hash_sha256", "prediction"),
        Index("ix_threat_logs_detected_at_risk", "detected_at", "risk_level"),
    )

    def to_dict(self) -> dict:
        """Serialise to a plain dict (useful for MongoDB logging and API responses)."""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_hash_md5": self.file_hash_md5,
            "file_hash_sha256": self.file_hash_sha256,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "detection_engine": self.detection_engine,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level.value if self.risk_level else None,
            "status": self.status.value if self.status else None,
            "yara_matches": self.yara_matches,
            "static_analysis_results": self.static_analysis_results,
            "suspicious_indicators": self.suspicious_indicators,
            "description": self.description,
            "recommended_action": self.recommended_action,
            "notes": self.notes,
            "detected_by_user_id": self.detected_by_user_id,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


# ---------------------------------------------------------------------------
# ThreatTimelineEvent — Chronological event log per threat
# ---------------------------------------------------------------------------

class ThreatTimelineEvent(Base):
    """
    Records significant events in the lifecycle of a threat detection.

    Examples: initial detection, status change to "under investigation",
    analyst note, escalation to SOC team, resolution.
    """

    __tablename__ = "threat_timeline_events"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    threat_id = Column(
        String(36),
        ForeignKey("threat_logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_type = Column(
        Enum(TimelineEventType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    description = Column(Text, nullable=False)

    # Who triggered this event (nullable for system-generated events)
    created_by = Column(String(255), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    # ---- Relationships ----
    threat = relationship("ThreatLog", back_populates="timeline_events")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "threat_id": self.threat_id,
            "event_type": self.event_type.value if self.event_type else None,
            "description": self.description,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
