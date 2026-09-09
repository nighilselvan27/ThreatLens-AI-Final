from typing import Tuple


def calculate_risk_score(confidence: float) -> Tuple[int, str]:
    """
    Calculate risk score and risk level based on AI confidence.
    """

    if confidence < 0 or confidence > 100:
        raise ValueError("Confidence must be between 0 and 100.")

    if confidence >= 90:
        return 95, "High Risk"

    elif confidence >= 75:
        return 80, "Medium Risk"

    elif confidence >= 50:
        return 60, "Low Risk"

    else:
        return 30, "Minimal Risk"
