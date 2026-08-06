from app.modules.threat_monitoring.repository import ThreatRepository


class ThreatReport:
    """
    Generates threat reports and dashboard statistics.
    """

    @staticmethod
    def generate_summary():
        """
        Returns overall threat statistics.
        """

        total = ThreatRepository.total_files()
        malware = ThreatRepository.get_malware_count()
        benign = ThreatRepository.get_benign_count()

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
            "benign_percentage": benign_percentage
        }

    @staticmethod
    def threat_timeline():
        """
        Returns all detections sorted by detection time.
        """

        threats = ThreatRepository.get_all_threats()

        threats.sort(
            key=lambda x: x.get("detected_at", "")
        )

        return threats
