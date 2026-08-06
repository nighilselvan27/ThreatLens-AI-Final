from app.modules.threat_monitoring.models import ThreatLog
from app.modules.threat_monitoring.repository import ThreatRepository
from app.modules.threat_monitoring.risk_score import calculate_risk_score


class ThreatMonitoringService:
    """
    Handles the business logic for threat monitoring.
    """

    @staticmethod
    def save_detection(filename: str,
                       prediction: str,
                       confidence: float,
                       file_hash: str = None):
        """
        Save a malware detection into MongoDB.
        """

        # Calculate risk score
        risk_score, risk_level = calculate_risk_score(confidence)

        # Create ThreatLog object
        threat = ThreatLog(
            filename=filename,
            file_hash=file_hash,
            prediction=prediction,
            confidence=confidence,
            risk_score=risk_score,
            risk_level=risk_level
        )

        # Save to database
        ThreatRepository.save_threat(threat)

        return {
            "message": "Threat stored successfully.",
            "filename": filename,
            "prediction": prediction,
            "confidence": confidence,
            "risk_score": risk_score,
            "risk_level": risk_level
        }

    @staticmethod
    def get_history():
        """
        Returns complete threat history.
        """
        return ThreatRepository.get_all_threats()

    @staticmethod
    def get_summary():
        """
        Returns dashboard summary.
        """

        total = ThreatRepository.total_files()
        malware = ThreatRepository.get_malware_count()
        benign = ThreatRepository.get_benign_count()

        return {
            "total_files": total,
            "malware_files": malware,
            "benign_files": benign
        }
