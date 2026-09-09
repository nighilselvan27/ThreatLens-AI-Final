"""
Legacy compatibility wrapper for the Threat Monitoring service.

This file originally contained stub imports that pointed to non-existent
modules. It now re-exports from the actual threat_monitoring package
so that any existing code that imports from here continues to work.

For new code, import directly from:
    app.modules.threat_monitoring.service.ThreatMonitoringService
    app.modules.threat_monitoring.models.ThreatLog
    app.modules.threat_monitoring.repository.ThreatRepository
    app.modules.threat_monitoring.risk_score.calculate_risk_score
"""

from app.modules.threat_monitoring.models import ThreatLog
from app.modules.threat_monitoring.repository import ThreatRepository
from app.modules.threat_monitoring.risk_score import calculate_risk_score
from app.modules.threat_monitoring.service import ThreatMonitoringService as _Service
from app.modules.threat_monitoring.schemas import ThreatLogCreate

from sqlalchemy.orm import Session


class ThreatMonitoringService:
    """
    Backward-compatible wrapper for the threat monitoring service.

    Preserves the original interface (save_detection, get_history, get_summary)
    while delegating to the full-featured service implementation.
    """

    @staticmethod
    def save_detection(
        db: Session,
        filename: str,
        prediction: str,
        confidence: float,
        file_hash: str = None,
    ):
        """
        Save a malware detection.

        This is the legacy interface. For the full API, use:
            ThreatMonitoringService.record_detection(db, ThreatLogCreate(...))
        """
        payload = ThreatLogCreate(
            filename=filename,
            prediction=prediction,
            confidence=confidence,
            file_hash_sha256=file_hash,
        )
        return _Service.record_detection(db, payload)

    @staticmethod
    def get_history(db: Session):
        """Returns complete threat history (unpaginated)."""
        result = _Service.get_threat_history(db, page=1, page_size=1000)
        return [item.model_dump() for item in result.items]

    @staticmethod
    def get_summary(db: Session):
        """Returns dashboard summary."""
        summary = _Service.get_dashboard_summary(db)
        return {
            "total_files": summary.total_files,
            "malware_files": summary.malware_files,
            "benign_files": summary.benign_files,
        }
