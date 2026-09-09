"""
PostgreSQL data access layer for the Threat Monitoring module.

All database queries and mutations for ThreatLog and ThreatTimelineEvent
are encapsulated here, keeping the service layer clean of raw SQLAlchemy
query construction.
"""

import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple

from sqlalchemy import func, case, text, desc, asc
from sqlalchemy.orm import Session, joinedload

from app.modules.threat_monitoring.models import (
    ThreatLog,
    ThreatTimelineEvent,
    ThreatStatus,
    RiskLevel,
    TimelineEventType,
)


class ThreatRepository:
    """Data access layer for threat monitoring records in PostgreSQL."""

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    @staticmethod
    def save_threat(db: Session, threat: ThreatLog) -> ThreatLog:
        """Persist a new ThreatLog to the database."""
        db.add(threat)
        db.commit()
        db.refresh(threat)
        return threat

    @staticmethod
    def add_timeline_event(
        db: Session,
        threat_id: str,
        event_type: TimelineEventType,
        description: str,
        created_by: Optional[str] = None,
    ) -> ThreatTimelineEvent:
        """Append a timeline event to a threat's history."""
        event = ThreatTimelineEvent(
            id=str(uuid.uuid4()),
            threat_id=threat_id,
            event_type=event_type,
            description=description,
            created_by=created_by,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    # ------------------------------------------------------------------
    # READ — Single
    # ------------------------------------------------------------------

    @staticmethod
    def get_threat_by_id(db: Session, threat_id: str) -> Optional[ThreatLog]:
        """Fetch a single threat by ID, eager-loading timeline events."""
        return (
            db.query(ThreatLog)
            .options(joinedload(ThreatLog.timeline_events))
            .filter(ThreatLog.id == threat_id)
            .first()
        )

    # ------------------------------------------------------------------
    # READ — Lists / Filtered queries
    # ------------------------------------------------------------------

    @staticmethod
    def get_all_threats(
        db: Session,
        *,
        prediction: Optional[str] = None,
        risk_level: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        sort_by: str = "detected_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ThreatLog], int]:
        """
        Retrieve a filtered, sorted, paginated list of threats.

        Returns:
            Tuple of (list of ThreatLog, total count matching filters).
        """
        query = db.query(ThreatLog)

        # --- Apply filters ---
        if prediction:
            query = query.filter(ThreatLog.prediction.ilike(f"%{prediction}%"))
        if risk_level:
            query = query.filter(ThreatLog.risk_level == risk_level)
        if status:
            query = query.filter(ThreatLog.status == status)
        if search:
            query = query.filter(
                (ThreatLog.filename.ilike(f"%{search}%"))
                | (ThreatLog.file_hash_sha256.ilike(f"%{search}%"))
                | (ThreatLog.prediction.ilike(f"%{search}%"))
            )
        if date_from:
            query = query.filter(ThreatLog.detected_at >= date_from)
        if date_to:
            query = query.filter(ThreatLog.detected_at <= date_to)

        # --- Count total before pagination ---
        total = query.count()

        # --- Sort ---
        sort_column = getattr(ThreatLog, sort_by, ThreatLog.detected_at)
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # --- Paginate ---
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    @staticmethod
    def get_threats_by_hash(db: Session, file_hash: str) -> List[ThreatLog]:
        """Find all detections of a file by its SHA-256 hash."""
        return (
            db.query(ThreatLog)
            .filter(ThreatLog.file_hash_sha256 == file_hash)
            .order_by(desc(ThreatLog.detected_at))
            .all()
        )

    @staticmethod
    def get_threat_timeline(db: Session, threat_id: str) -> List[ThreatTimelineEvent]:
        """Get all timeline events for a threat, ordered chronologically."""
        return (
            db.query(ThreatTimelineEvent)
            .filter(ThreatTimelineEvent.threat_id == threat_id)
            .order_by(asc(ThreatTimelineEvent.created_at))
            .all()
        )

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    @staticmethod
    def update_threat_status(
        db: Session,
        threat_id: str,
        new_status: ThreatStatus,
    ) -> Optional[ThreatLog]:
        """Update the status of a threat."""
        threat = db.query(ThreatLog).filter(ThreatLog.id == threat_id).first()
        if not threat:
            return None

        threat.status = new_status
        threat.updated_at = datetime.now(timezone.utc)

        if new_status in (ThreatStatus.RESOLVED, ThreatStatus.FALSE_POSITIVE):
            threat.resolved_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(threat)
        return threat

    @staticmethod
    def update_threat(
        db: Session,
        threat_id: str,
        **kwargs,
    ) -> Optional[ThreatLog]:
        """Update arbitrary fields on a threat."""
        threat = db.query(ThreatLog).filter(ThreatLog.id == threat_id).first()
        if not threat:
            return None

        for key, value in kwargs.items():
            if hasattr(threat, key) and value is not None:
                setattr(threat, key, value)

        threat.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(threat)
        return threat

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    @staticmethod
    def delete_threat(db: Session, threat_id: str) -> bool:
        """Delete a threat and its associated timeline events."""
        threat = db.query(ThreatLog).filter(ThreatLog.id == threat_id).first()
        if not threat:
            return False
        db.delete(threat)
        db.commit()
        return True

    # ------------------------------------------------------------------
    # AGGREGATIONS — Dashboard & Reporting
    # ------------------------------------------------------------------

    @staticmethod
    def total_files(db: Session) -> int:
        """Total number of scanned files."""
        return db.query(func.count(ThreatLog.id)).scalar() or 0

    @staticmethod
    def get_malware_count(db: Session) -> int:
        """Count of files classified as malware (not benign)."""
        return (
            db.query(func.count(ThreatLog.id))
            .filter(ThreatLog.prediction.notilike("benign"))
            .filter(ThreatLog.prediction.notilike("clean"))
            .filter(ThreatLog.prediction.notilike("safe"))
            .scalar() or 0
        )

    @staticmethod
    def get_benign_count(db: Session) -> int:
        """Count of files classified as benign."""
        return (
            db.query(func.count(ThreatLog.id))
            .filter(
                (ThreatLog.prediction.ilike("benign"))
                | (ThreatLog.prediction.ilike("clean"))
                | (ThreatLog.prediction.ilike("safe"))
            )
            .scalar() or 0
        )

    @staticmethod
    def get_count_by_risk_level(db: Session, risk_level: str) -> int:
        """Count of threats at a specific risk level."""
        return (
            db.query(func.count(ThreatLog.id))
            .filter(ThreatLog.risk_level == risk_level)
            .scalar() or 0
        )

    @staticmethod
    def get_active_threat_count(db: Session) -> int:
        """Count of threats that are not yet resolved or dismissed."""
        resolved_statuses = [
            ThreatStatus.RESOLVED.value,
            ThreatStatus.FALSE_POSITIVE.value,
        ]
        return (
            db.query(func.count(ThreatLog.id))
            .filter(ThreatLog.status.notin_(resolved_statuses))
            .scalar() or 0
        )

    @staticmethod
    def get_resolved_threat_count(db: Session) -> int:
        """Count of resolved or false-positive threats."""
        resolved_statuses = [
            ThreatStatus.RESOLVED.value,
            ThreatStatus.FALSE_POSITIVE.value,
        ]
        return (
            db.query(func.count(ThreatLog.id))
            .filter(ThreatLog.status.in_(resolved_statuses))
            .scalar() or 0
        )

    @staticmethod
    def get_threats_by_family(db: Session, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get malware family breakdown (top N families by detection count).

        Returns:
            List of (family_name, count) tuples.
        """
        results = (
            db.query(ThreatLog.prediction, func.count(ThreatLog.id).label("count"))
            .filter(ThreatLog.prediction.notilike("benign"))
            .filter(ThreatLog.prediction.notilike("clean"))
            .filter(ThreatLog.prediction.notilike("safe"))
            .group_by(ThreatLog.prediction)
            .order_by(desc("count"))
            .limit(limit)
            .all()
        )
        return [(row[0], row[1]) for row in results]

    @staticmethod
    def get_status_distribution(db: Session) -> dict:
        """Get count of threats per status."""
        results = (
            db.query(ThreatLog.status, func.count(ThreatLog.id).label("count"))
            .group_by(ThreatLog.status)
            .all()
        )
        return {
            (row[0].value if hasattr(row[0], "value") else row[0]): row[1]
            for row in results
        }

    @staticmethod
    def get_detection_trend(db: Session, days: int = 30) -> List[dict]:
        """
        Get daily detection counts for the last N days.

        Returns:
            List of dicts with keys: date, total, malware, benign.
        """
        start_date = datetime.now(timezone.utc) - timedelta(days=days)

        # Get all threats in the date range
        threats = (
            db.query(ThreatLog)
            .filter(ThreatLog.detected_at >= start_date)
            .all()
        )

        # Aggregate by day
        daily_counts = {}
        for threat in threats:
            if threat.detected_at:
                day_key = threat.detected_at.strftime("%Y-%m-%d")
            else:
                continue

            if day_key not in daily_counts:
                daily_counts[day_key] = {"date": day_key, "total": 0, "malware": 0, "benign": 0}

            daily_counts[day_key]["total"] += 1

            prediction_lower = (threat.prediction or "").lower()
            if prediction_lower in ("benign", "clean", "safe"):
                daily_counts[day_key]["benign"] += 1
            else:
                daily_counts[day_key]["malware"] += 1

        # Fill in missing days with zeros
        result = []
        for i in range(days):
            day = (datetime.now(timezone.utc) - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
            if day in daily_counts:
                result.append(daily_counts[day])
            else:
                result.append({"date": day, "total": 0, "malware": 0, "benign": 0})

        return result

    @staticmethod
    def get_recent_critical_threats(db: Session, limit: int = 5) -> List[ThreatLog]:
        """Get the most recent critical/high-risk threats."""
        return (
            db.query(ThreatLog)
            .filter(
                ThreatLog.risk_level.in_([
                    RiskLevel.CRITICAL.value,
                    RiskLevel.HIGH.value,
                ])
            )
            .order_by(desc(ThreatLog.detected_at))
            .limit(limit)
            .all()
        )
