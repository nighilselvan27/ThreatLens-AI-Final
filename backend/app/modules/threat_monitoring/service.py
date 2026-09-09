"""
Business logic layer for the Threat Monitoring module.

Orchestrates the full detection → logging → alerting workflow:
    1. Accept an AI prediction result
    2. Calculate the risk score
    3. Persist the detection in PostgreSQL (ThreatLog)
    4. Log the full event in MongoDB (detection_logs)
    5. Create an initial timeline event
    6. Trigger an alert if the detection is malware (via alert_integration)
    7. Return the enriched detection result

Also provides query/aggregation methods for the dashboard and reports.
"""

import math
import logging
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.orm import Session

from app.modules.threat_monitoring.models import (
    ThreatLog,
    ThreatTimelineEvent,
    ThreatStatus,
    RiskLevel,
    TimelineEventType,
)
from app.modules.threat_monitoring.schemas import (
    ThreatLogCreate,
    ThreatLogResponse,
    ThreatSummaryResponse,
    ThreatTrendPoint,
    ThreatTrendResponse,
    MalwareFamilyCount,
    MalwareFamilyBreakdownResponse,
    ThreatReportResponse,
    PaginatedThreatResponse,
)
from app.modules.threat_monitoring.repository import ThreatRepository
from app.modules.threat_monitoring.mongo_repository import MongoThreatLogger
from app.modules.threat_monitoring.risk_score import calculate_risk_score, get_recommended_action

logger = logging.getLogger("threat_monitoring.service")


# ---------------------------------------------------------------------------
# Benign detection helpers
# ---------------------------------------------------------------------------

_BENIGN_PREDICTIONS = {"benign", "clean", "safe", "not malicious"}


def _is_benign(prediction: str) -> bool:
    return (prediction or "").strip().lower() in _BENIGN_PREDICTIONS


# ---------------------------------------------------------------------------
# Service Class
# ---------------------------------------------------------------------------

class ThreatMonitoringService:
    """
    Handles the business logic for threat monitoring.

    All methods receive a SQLAlchemy `db` session and operate synchronously.
    """

    # ------------------------------------------------------------------
    # CORE — Record a new detection
    # ------------------------------------------------------------------

    @staticmethod
    def record_detection(db: Session, payload: ThreatLogCreate) -> dict:
        """
        Full detection recording workflow:
            1. Calculate risk score
            2. Save to PostgreSQL
            3. Log to MongoDB
            4. Create timeline event
            5. Trigger alert (if malware)
            6. Return enriched result

        Args:
            db: SQLAlchemy database session.
            payload: Validated detection input.

        Returns:
            Dict with the saved detection data and metadata.
        """

        # 1. Calculate risk score
        risk_score, risk_level = calculate_risk_score(
            confidence=payload.confidence,
            prediction=payload.prediction,
            yara_matches=payload.yara_matches,
            suspicious_indicators=payload.suspicious_indicators,
        )

        # Generate recommended action
        recommended_action = payload.recommended_action or get_recommended_action(
            risk_level, payload.prediction
        )

        # Generate description if not provided
        description = payload.description
        if not description:
            if _is_benign(payload.prediction):
                description = f"File '{payload.filename}' scanned and classified as benign."
            else:
                description = (
                    f"File '{payload.filename}' classified as {payload.prediction} "
                    f"with {payload.confidence}% confidence. Risk level: {risk_level}."
                )

        # Determine initial status
        initial_status = ThreatStatus.DETECTED
        if _is_benign(payload.prediction):
            initial_status = ThreatStatus.RESOLVED

        # 2. Create and save ThreatLog to PostgreSQL
        threat = ThreatLog(
            filename=payload.filename,
            file_hash_md5=payload.file_hash_md5,
            file_hash_sha256=payload.file_hash_sha256,
            file_size=payload.file_size,
            file_type=payload.file_type,
            prediction=payload.prediction,
            confidence=payload.confidence,
            detection_engine=payload.detection_engine,
            risk_score=risk_score,
            risk_level=risk_level,
            status=initial_status,
            yara_matches=payload.yara_matches,
            static_analysis_results=payload.static_analysis_results,
            suspicious_indicators=payload.suspicious_indicators,
            description=description,
            recommended_action=recommended_action,
            notes=payload.notes,
            detected_by_user_id=payload.detected_by_user_id,
        )

        saved_threat = ThreatRepository.save_threat(db, threat)
        logger.info(
            "Detection recorded: %s -> %s (risk: %s/%s, id: %s)",
            payload.filename,
            payload.prediction,
            risk_score,
            risk_level,
            saved_threat.id,
        )

        # 3. Log to MongoDB (async-safe, won't fail if MongoDB is down)
        mongo_log_id = MongoThreatLogger.log_detection(
            threat_id=saved_threat.id,
            filename=payload.filename,
            prediction=payload.prediction,
            confidence=payload.confidence,
            risk_score=risk_score,
            risk_level=risk_level,
            detection_engine=payload.detection_engine,
            file_hash_md5=payload.file_hash_md5,
            file_hash_sha256=payload.file_hash_sha256,
            file_size=payload.file_size,
            file_type=payload.file_type,
            yara_matches=payload.yara_matches,
            static_analysis_results=payload.static_analysis_results,
            suspicious_indicators=payload.suspicious_indicators,
            raw_payload=payload.model_dump(),
            detected_by_user_id=payload.detected_by_user_id,
        )

        # 4. Create initial timeline event
        ThreatRepository.add_timeline_event(
            db=db,
            threat_id=saved_threat.id,
            event_type=TimelineEventType.DETECTED,
            description=(
                f"{'Malware' if not _is_benign(payload.prediction) else 'File'} detected: "
                f"{payload.prediction} (confidence: {payload.confidence}%, "
                f"risk score: {risk_score})"
            ),
            created_by="system",
        )

        # 5. Trigger alert if malware detected
        alert_result = None
        if not _is_benign(payload.prediction):
            try:
                from app.modules.threat_monitoring.alert_integration import trigger_alert_for_detection
                alert_result = trigger_alert_for_detection(
                    db=db,
                    threat=saved_threat,
                    risk_level=risk_level,
                )
                if alert_result:
                    # Add alert timeline event
                    ThreatRepository.add_timeline_event(
                        db=db,
                        threat_id=saved_threat.id,
                        event_type=TimelineEventType.ALERT_CREATED,
                        description=f"Security alert created for {payload.prediction} detection.",
                        created_by="system",
                    )
            except Exception as e:
                logger.warning("Could not trigger alert: %s", str(e))

        # 6. Return enriched result
        return {
            "message": "Detection recorded successfully.",
            "threat_id": saved_threat.id,
            "filename": payload.filename,
            "prediction": payload.prediction,
            "confidence": payload.confidence,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "status": initial_status.value,
            "recommended_action": recommended_action,
            "mongo_log_id": mongo_log_id,
            "alert_triggered": alert_result is not None,
            "detected_at": saved_threat.detected_at.isoformat() if saved_threat.detected_at else None,
        }

    # ------------------------------------------------------------------
    # QUERIES — Single threat
    # ------------------------------------------------------------------

    @staticmethod
    def get_threat_detail(db: Session, threat_id: str) -> Optional[ThreatLogResponse]:
        """Get a single threat with its full timeline."""
        threat = ThreatRepository.get_threat_by_id(db, threat_id)
        if not threat:
            return None
        return ThreatLogResponse.from_orm_threat(threat, include_timeline=True)

    # ------------------------------------------------------------------
    # QUERIES — Paginated list
    # ------------------------------------------------------------------

    @staticmethod
    def get_threat_history(
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
    ) -> PaginatedThreatResponse:
        """Get paginated, filtered threat history."""
        items, total = ThreatRepository.get_all_threats(
            db,
            prediction=prediction,
            risk_level=risk_level,
            status=status,
            search=search,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size,
        )

        total_pages = math.ceil(total / page_size) if page_size > 0 else 0

        return PaginatedThreatResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=[ThreatLogResponse.from_orm_threat(t) for t in items],
        )

    # ------------------------------------------------------------------
    # QUERIES — Malware tracking (by hash)
    # ------------------------------------------------------------------

    @staticmethod
    def track_malware(db: Session, file_hash: str) -> List[ThreatLogResponse]:
        """Find all detections of the same file by SHA-256 hash."""
        threats = ThreatRepository.get_threats_by_hash(db, file_hash)
        return [ThreatLogResponse.from_orm_threat(t) for t in threats]

    # ------------------------------------------------------------------
    # QUERIES — Timeline
    # ------------------------------------------------------------------

    @staticmethod
    def get_threat_timeline(db: Session, threat_id: str) -> Optional[list]:
        """Get the chronological timeline for a specific threat."""
        threat = ThreatRepository.get_threat_by_id(db, threat_id)
        if not threat:
            return None
        events = ThreatRepository.get_threat_timeline(db, threat_id)
        return [evt.to_dict() for evt in events]

    # ------------------------------------------------------------------
    # STATUS UPDATES
    # ------------------------------------------------------------------

    @staticmethod
    def update_threat_status(
        db: Session,
        threat_id: str,
        new_status: str,
        updated_by: Optional[str] = None,
    ) -> Optional[ThreatLogResponse]:
        """
        Update a threat's status and log the change on the timeline.
        """
        # Validate status
        try:
            status_enum = ThreatStatus(new_status)
        except ValueError:
            return None

        threat = ThreatRepository.update_threat_status(db, threat_id, status_enum)
        if not threat:
            return None

        # Add timeline event for the status change
        ThreatRepository.add_timeline_event(
            db=db,
            threat_id=threat_id,
            event_type=TimelineEventType.STATUS_CHANGED,
            description=f"Status changed to '{new_status}' by {updated_by or 'system'}.",
            created_by=updated_by,
        )

        return ThreatLogResponse.from_orm_threat(threat)

    @staticmethod
    def resolve_threat(
        db: Session,
        threat_id: str,
        resolved_by: Optional[str] = None,
    ) -> Optional[ThreatLogResponse]:
        """Mark a threat as resolved."""
        threat = ThreatRepository.update_threat_status(db, threat_id, ThreatStatus.RESOLVED)
        if not threat:
            return None

        ThreatRepository.add_timeline_event(
            db=db,
            threat_id=threat_id,
            event_type=TimelineEventType.RESOLVED,
            description=f"Threat resolved by {resolved_by or 'system'}.",
            created_by=resolved_by,
        )

        return ThreatLogResponse.from_orm_threat(threat)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    @staticmethod
    def delete_threat(db: Session, threat_id: str) -> bool:
        """Delete a threat and all associated data."""
        return ThreatRepository.delete_threat(db, threat_id)

    # ------------------------------------------------------------------
    # DASHBOARD — Summary
    # ------------------------------------------------------------------

    @staticmethod
    def get_dashboard_summary(db: Session) -> ThreatSummaryResponse:
        """Get aggregated dashboard statistics."""
        total = ThreatRepository.total_files(db)
        malware = ThreatRepository.get_malware_count(db)
        benign = ThreatRepository.get_benign_count(db)

        malware_pct = round((malware / total) * 100, 2) if total > 0 else 0.0
        benign_pct = round((benign / total) * 100, 2) if total > 0 else 0.0

        return ThreatSummaryResponse(
            total_files=total,
            malware_files=malware,
            benign_files=benign,
            malware_percentage=malware_pct,
            benign_percentage=benign_pct,
            critical_threats=ThreatRepository.get_count_by_risk_level(db, RiskLevel.CRITICAL.value),
            high_risk_threats=ThreatRepository.get_count_by_risk_level(db, RiskLevel.HIGH.value),
            medium_risk_threats=ThreatRepository.get_count_by_risk_level(db, RiskLevel.MEDIUM.value),
            low_risk_threats=ThreatRepository.get_count_by_risk_level(db, RiskLevel.LOW.value),
            active_threats=ThreatRepository.get_active_threat_count(db),
            resolved_threats=ThreatRepository.get_resolved_threat_count(db),
        )

    # ------------------------------------------------------------------
    # DASHBOARD — Trends
    # ------------------------------------------------------------------

    @staticmethod
    def get_detection_trends(db: Session, days: int = 30) -> ThreatTrendResponse:
        """Get daily detection trends for the last N days."""
        raw_data = ThreatRepository.get_detection_trend(db, days)
        data_points = [
            ThreatTrendPoint(
                date=d["date"],
                total=d["total"],
                malware=d["malware"],
                benign=d["benign"],
            )
            for d in raw_data
        ]
        return ThreatTrendResponse(days=days, data=data_points)

    # ------------------------------------------------------------------
    # DASHBOARD — Family breakdown
    # ------------------------------------------------------------------

    @staticmethod
    def get_malware_family_breakdown(db: Session, limit: int = 10) -> MalwareFamilyBreakdownResponse:
        """Get malware family distribution for pie charts."""
        families_raw = ThreatRepository.get_threats_by_family(db, limit)
        total_malware = sum(count for _, count in families_raw)

        families = [
            MalwareFamilyCount(
                family=family,
                count=count,
                percentage=round((count / total_malware) * 100, 2) if total_malware > 0 else 0.0,
            )
            for family, count in families_raw
        ]

        return MalwareFamilyBreakdownResponse(
            total_malware=total_malware,
            families=families,
        )

    # ------------------------------------------------------------------
    # REPORTS
    # ------------------------------------------------------------------

    @staticmethod
    def generate_threat_report(
        db: Session,
        days: int = 30,
    ) -> ThreatReportResponse:
        """
        Generate a comprehensive threat report combining:
            - Summary statistics
            - Detection trends
            - Malware family breakdown
            - Recent critical threats
            - Status distribution
        """
        summary = ThreatMonitoringService.get_dashboard_summary(db)
        trends = ThreatMonitoringService.get_detection_trends(db, days)
        family_breakdown = ThreatMonitoringService.get_malware_family_breakdown(db)

        recent_critical = ThreatRepository.get_recent_critical_threats(db, limit=5)
        status_dist = ThreatRepository.get_status_distribution(db)

        return ThreatReportResponse(
            generated_at=datetime.now(timezone.utc),
            summary=summary,
            trends=trends,
            family_breakdown=family_breakdown,
            recent_critical=[ThreatLogResponse.from_orm_threat(t) for t in recent_critical],
            status_distribution=status_dist,
        )
