"""
Pydantic request/response schemas for the Threat Monitoring REST API.

These schemas validate incoming payloads and structure outgoing JSON responses.
They are intentionally decoupled from the SQLAlchemy models so the API surface
can evolve independently of the database schema.
"""

from datetime import datetime
from typing import Optional, List, Any
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums (mirror the SQLAlchemy enums for the API layer)
# ---------------------------------------------------------------------------

class ThreatStatusEnum(str, Enum):
    DETECTED = "detected"
    QUARANTINED = "quarantined"
    UNDER_INVESTIGATION = "under_investigation"
    CONFIRMED = "confirmed"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"
    MONITORING = "monitoring"


class RiskLevelEnum(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class TimelineEventTypeEnum(str, Enum):
    DETECTED = "detected"
    ANALYZED = "analyzed"
    ESCALATED = "escalated"
    STATUS_CHANGED = "status_changed"
    NOTE_ADDED = "note_added"
    RESOLVED = "resolved"
    REOPENED = "reopened"
    ALERT_CREATED = "alert_created"


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------

class ThreatLogCreate(BaseModel):
    """Payload for recording a new malware detection event."""

    filename: str = Field(..., min_length=1, max_length=500, description="Original filename")
    file_hash_md5: Optional[str] = Field(None, max_length=32, description="MD5 hash of the file")
    file_hash_sha256: Optional[str] = Field(None, max_length=64, description="SHA-256 hash of the file")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    file_type: Optional[str] = Field(None, max_length=50, description="File extension / type")

    prediction: str = Field(..., min_length=1, max_length=100, description="AI prediction (malware family or 'Benign')")
    confidence: float = Field(..., ge=0.0, le=100.0, description="AI confidence percentage (0-100)")
    detection_engine: Optional[str] = Field("ThreatLens AI", max_length=100)

    # Optional static analysis artifacts
    yara_matches: Optional[List[str]] = Field(None, description="List of matched YARA rule names")
    static_analysis_results: Optional[dict] = Field(None, description="Full static analysis payload")
    suspicious_indicators: Optional[dict] = Field(None, description="Suspicious URLs, IPs, strings")

    description: Optional[str] = None
    recommended_action: Optional[str] = None
    notes: Optional[str] = None

    # User who triggered the scan (optional — system scans may not have a user)
    detected_by_user_id: Optional[int] = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "filename": "invoice.exe",
                    "file_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                    "file_size": 245760,
                    "file_type": "exe",
                    "prediction": "Trojan",
                    "confidence": 87.5,
                    "detection_engine": "ThreatLens AI",
                    "yara_matches": ["MALWARE_Trojan_Generic", "SUSPICIOUS_PowerShell_Invoke"],
                    "description": "Suspicious PE file with encoded PowerShell commands",
                    "recommended_action": "Escalate to Security Analyst for Investigation",
                }
            ]
        }
    )


class ThreatLogUpdate(BaseModel):
    """Payload for updating threat status and notes."""

    status: Optional[ThreatStatusEnum] = None
    notes: Optional[str] = None
    recommended_action: Optional[str] = None


class ThreatStatusUpdate(BaseModel):
    """Simple status-only update payload."""

    status: ThreatStatusEnum = Field(..., description="New status for the threat")


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------

class ThreatTimelineEventResponse(BaseModel):
    """Single timeline event in a threat's history."""

    id: str
    threat_id: str
    event_type: str
    description: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ThreatLogResponse(BaseModel):
    """Full threat detection record returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_hash_md5: Optional[str] = None
    file_hash_sha256: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None

    prediction: str
    confidence: float
    detection_engine: Optional[str] = None

    risk_score: int
    risk_level: str

    status: str

    yara_matches: Optional[List[Any]] = None
    static_analysis_results: Optional[dict] = None
    suspicious_indicators: Optional[dict] = None

    description: Optional[str] = None
    recommended_action: Optional[str] = None
    notes: Optional[str] = None

    detected_by_user_id: Optional[int] = None

    detected_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    timeline: Optional[List[ThreatTimelineEventResponse]] = None

    @classmethod
    def from_orm_threat(cls, threat, include_timeline: bool = False):
        """Build response from a ThreatLog ORM instance."""
        data = {
            "id": threat.id,
            "filename": threat.filename,
            "file_hash_md5": threat.file_hash_md5,
            "file_hash_sha256": threat.file_hash_sha256,
            "file_size": threat.file_size,
            "file_type": threat.file_type,
            "prediction": threat.prediction,
            "confidence": threat.confidence,
            "detection_engine": threat.detection_engine,
            "risk_score": threat.risk_score,
            "risk_level": threat.risk_level.value if hasattr(threat.risk_level, "value") else threat.risk_level,
            "status": threat.status.value if hasattr(threat.status, "value") else threat.status,
            "yara_matches": threat.yara_matches,
            "static_analysis_results": threat.static_analysis_results,
            "suspicious_indicators": threat.suspicious_indicators,
            "description": threat.description,
            "recommended_action": threat.recommended_action,
            "notes": threat.notes,
            "detected_by_user_id": threat.detected_by_user_id,
            "detected_at": threat.detected_at,
            "updated_at": threat.updated_at,
            "resolved_at": threat.resolved_at,
        }

        if include_timeline and hasattr(threat, "timeline_events") and threat.timeline_events:
            data["timeline"] = [
                ThreatTimelineEventResponse(
                    id=evt.id,
                    threat_id=evt.threat_id,
                    event_type=evt.event_type.value if hasattr(evt.event_type, "value") else evt.event_type,
                    description=evt.description,
                    created_by=evt.created_by,
                    created_at=evt.created_at,
                )
                for evt in threat.timeline_events
            ]

        return cls(**data)


class ThreatSummaryResponse(BaseModel):
    """Dashboard summary statistics."""

    total_files: int = 0
    malware_files: int = 0
    benign_files: int = 0
    malware_percentage: float = 0.0
    benign_percentage: float = 0.0
    critical_threats: int = 0
    high_risk_threats: int = 0
    medium_risk_threats: int = 0
    low_risk_threats: int = 0
    active_threats: int = 0        # threats not yet resolved
    resolved_threats: int = 0


class ThreatTrendPoint(BaseModel):
    """A single data point in a time-series trend."""

    date: str                       # ISO date string (YYYY-MM-DD)
    total: int = 0
    malware: int = 0
    benign: int = 0


class ThreatTrendResponse(BaseModel):
    """Time-series detection trend data for charts."""

    days: int
    data: List[ThreatTrendPoint]


class MalwareFamilyCount(BaseModel):
    """Count of detections per malware family."""

    family: str
    count: int
    percentage: float = 0.0


class MalwareFamilyBreakdownResponse(BaseModel):
    """Breakdown of detections by malware family (pie chart data)."""

    total_malware: int = 0
    families: List[MalwareFamilyCount]


class ThreatReportResponse(BaseModel):
    """Comprehensive threat report combining summary, trends, and breakdowns."""

    generated_at: datetime
    summary: ThreatSummaryResponse
    trends: ThreatTrendResponse
    family_breakdown: MalwareFamilyBreakdownResponse
    recent_critical: List[ThreatLogResponse]         # latest critical threats
    status_distribution: dict                        # status -> count


class PaginatedThreatResponse(BaseModel):
    """Paginated list of threat detections."""

    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[ThreatLogResponse]


class MongoDetectionLogResponse(BaseModel):
    """MongoDB detection log entry response."""

    id: str
    threat_id: Optional[str] = None
    filename: str
    prediction: str
    confidence: float
    risk_score: int
    risk_level: str
    detection_engine: Optional[str] = None
    raw_payload: Optional[dict] = None
    logged_at: Optional[datetime] = None


class MongoLogsListResponse(BaseModel):
    """Paginated MongoDB logs response."""

    total: int
    limit: int
    offset: int
    items: List[MongoDetectionLogResponse]
