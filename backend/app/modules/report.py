"""
Legacy compatibility wrapper for threat reporting.

Re-exports from the actual threat_monitoring package.
For new code, use ThreatMonitoringService.generate_threat_report() directly.
"""

from app.modules.threat_monitoring.repository import ThreatRepository
from app.modules.threat_monitoring.service import ThreatMonitoringService

from sqlalchemy.orm import Session


class ThreatReport:
    """
    Generates threat reports and dashboard statistics.
    """

    @staticmethod
    def generate_summary(db: Session):
        """
        Returns overall threat statistics.
        """
        summary = ThreatMonitoringService.get_dashboard_summary(db)
        total = summary.total_files
        malware = summary.malware_files
        benign = summary.benign_files

        if total == 0:
            malware_percentage = 0
            benign_percentage = 0
        else:
            malware_percentage = round((malware / total) * 100, 2)
            benign_percentage = round((benign / total) * 100, 2)

        return {
            "total_files": total,
            "malware_files": malware,
            "benign_files": benign,
            "malware_percentage": malware_percentage,
            "benign_percentage": benign_percentage,
        }

    @staticmethod
    def threat_timeline(db: Session):
        """
        Returns all detections sorted by detection time.
        """
        result = ThreatMonitoringService.get_threat_history(
            db,
            sort_by="detected_at",
            sort_order="asc",
            page=1,
            page_size=1000,
        )
        return [item.model_dump() for item in result.items]
