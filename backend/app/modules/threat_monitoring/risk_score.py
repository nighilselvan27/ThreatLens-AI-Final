"""
Enhanced multi-factor risk score calculator.

Computes a risk score (0–100) and risk level based on:
    1. AI model confidence (primary factor)
    2. Malware family severity bonus
    3. Suspicious indicator bonus (YARA matches, malicious URLs, etc.)

This replaces the simpler version in backend/app/modules/risk_score.py with
a richer scoring model.
"""

from typing import Tuple, Optional, List


# ---------------------------------------------------------------------------
# Malware family severity weights
# ---------------------------------------------------------------------------

_FAMILY_SEVERITY_BONUS = {
    "ransomware": 15,
    "rootkit": 15,
    "backdoor": 12,
    "trojan": 10,
    "worm": 10,
    "spyware": 8,
    "keylogger": 8,
    "botnet": 8,
    "exploit": 7,
    "rat": 10,          # Remote Access Trojan
    "dropper": 7,
    "downloader": 5,
    "adware": 3,
    "pup": 2,           # Potentially Unwanted Program
}

# ---------------------------------------------------------------------------
# Risk level thresholds
# ---------------------------------------------------------------------------

_RISK_THRESHOLDS = [
    (85, "critical"),
    (70, "high"),
    (50, "medium"),
    (30, "low"),
    (0,  "minimal"),
]


def calculate_risk_score(
    confidence: float,
    prediction: Optional[str] = None,
    yara_matches: Optional[List[str]] = None,
    suspicious_indicators: Optional[dict] = None,
) -> Tuple[int, str]:
    """
    Calculate a risk score and risk level.

    Args:
        confidence: AI model confidence percentage (0–100).
        prediction: Predicted malware family name (e.g. "Trojan", "Ransomware").
                    Case-insensitive. "Benign" / "Clean" predictions get score 0.
        yara_matches: List of matched YARA rule names. Each match adds +2 (max +10).
        suspicious_indicators: Dict of suspicious findings. Each category adds +2 (max +8).

    Returns:
        Tuple of (risk_score: int [0–100], risk_level: str).

    Raises:
        ValueError: If confidence is outside the 0–100 range.
    """

    if confidence < 0 or confidence > 100:
        raise ValueError("Confidence must be between 0 and 100.")

    # Benign predictions always return minimal risk
    if prediction and prediction.strip().lower() in {"benign", "clean", "safe", "not malicious"}:
        return 0, "minimal"

    # --- Base score from confidence ---
    base_score = confidence * 0.7  # 70% weight to AI confidence

    # --- Family severity bonus ---
    family_bonus = 0
    if prediction:
        family_key = prediction.strip().lower()
        family_bonus = _FAMILY_SEVERITY_BONUS.get(family_key, 5)  # default +5 for unknown families

    # --- YARA match bonus ---
    yara_bonus = 0
    if yara_matches:
        yara_bonus = min(len(yara_matches) * 2, 10)  # +2 per match, max +10

    # --- Suspicious indicator bonus ---
    indicator_bonus = 0
    if suspicious_indicators:
        # Each category of suspicious indicator adds +2
        indicator_bonus = min(len(suspicious_indicators) * 2, 8)  # max +8

    # --- Compute final score ---
    raw_score = base_score + family_bonus + yara_bonus + indicator_bonus
    final_score = max(0, min(100, round(raw_score)))

    # --- Determine risk level ---
    risk_level = "minimal"
    for threshold, level in _RISK_THRESHOLDS:
        if final_score >= threshold:
            risk_level = level
            break

    return final_score, risk_level


def get_recommended_action(risk_level: str, prediction: str) -> str:
    """
    Generate a recommended action based on risk level and prediction.

    Args:
        risk_level: One of "critical", "high", "medium", "low", "minimal".
        prediction: Malware family name or "Benign".

    Returns:
        Human-readable recommended action string.
    """

    actions = {
        "critical": f"IMMEDIATE ACTION REQUIRED: Quarantine the file and escalate to SOC team. "
                     f"Confirmed {prediction} detection with critical risk.",
        "high": f"Escalate to Security Analyst for investigation. "
                f"High-confidence {prediction} detection requires manual review.",
        "medium": f"Schedule investigation. {prediction} detection with moderate risk. "
                  f"Review static analysis results and YARA matches.",
        "low": f"Monitor and log. {prediction} detected with low confidence. "
               f"May require additional scanning.",
        "minimal": f"No immediate action required. Detection logged for reference.",
    }

    return actions.get(risk_level, "Review detection details and assess threat manually.")
