class RiskScorer:
    """
    Converts the ensemble malware probability
    into a risk score and risk level.
    """

    @staticmethod
    def calculate_risk_score(malware_probability):
        """
        Convert malware probability [0, 1]
        into a risk score [0, 100].
        """

        probability = max(0.0, min(1.0, malware_probability))

        return round(probability * 100, 2)

    @staticmethod
    def get_risk_level(risk_score):
        """
        Convert risk score into a human-readable
        risk category.
        """

        if risk_score < 25:
            return "LOW"

        elif risk_score < 50:
            return "MEDIUM"

        elif risk_score < 75:
            return "HIGH"

        else:
            return "CRITICAL"

    @staticmethod
    def get_verdict(malware_probability, threshold=0.5):
        """
        Convert model probability into a binary verdict.
        """

        if malware_probability >= threshold:
            return "MALWARE"

        return "BENIGN"

    @classmethod
    def analyze(cls, malware_probability, threshold=0.5):
        """
        Generate the complete AI risk analysis.
        """

        risk_score = cls.calculate_risk_score(
            malware_probability
        )

        risk_level = cls.get_risk_level(
            risk_score
        )

        verdict = cls.get_verdict(
            malware_probability,
            threshold
        )

        return {
            "verdict": verdict,
            "malware_probability": round(
                malware_probability,
                4
            ),
            "risk_score": risk_score,
            "risk_level": risk_level
        }