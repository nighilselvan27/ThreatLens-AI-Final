"""
Adapter: AI Classification module -> Alert & Notification (Member 6).

CONFIRMED CONTRACT (per team review, 2026-09-08):
    {
      "detection_id": str,       # stable id -> used for exact-match dedup
      "risk_score": float,       # 0-100
      "file_id": str,
      "malware_family": str,
      "malware_probability": float,  # 0-1 (NOT a 0-100 confidence_score)
      "source_module": "classification"
    }

This replaces an earlier draft of this adapter that assumed a
`confidence_score` (0-100) + `risk_level` string ("High Risk", etc.)
shape from Member 5's Threat Monitoring module -- the AI/Classification
team confirmed the real field is `malware_probability` on a 0-1 scale,
and there is no `risk_level` string at all.

SEVERITY MAPPING (open question raised by the AI team -- see note below):
This adapter derives alert `severity` from `risk_score` (0-100), using
the same style of thresholds the classification module itself uses
internally (documented assumption -- confirm/adjust with the AI team if
their thresholds differ):
    risk_score >= 90 -> CRITICAL
    risk_score >= 75 -> HIGH
    risk_score >= 50 -> MEDIUM
    risk_score <  50 -> LOW
Severity.INFO is reserved for non-detection system notices and is never
produced here.

OPEN QUESTION (confirm with team before relying on this in production):
should alert severity thresholds always mirror the AI's own risk levels
1:1, or are they allowed to diverge (e.g. because an analyst-facing
"critical" means something operationally different from a model's
"high risk_score")? This adapter currently keeps them *related but
independently configurable* -- change ALERT_SEVERITY_THRESHOLDS below
if the team decides they should always match exactly.

LOW-PROBABILITY GATE:
Alerts are only created when malware_probability is missing OR >=
ALERT_MIN_MALWARE_PROBABILITY (default 0.5). This replaces the old
`is_benign(prediction)` string check, since the new contract has no
"prediction"/"benign" field at all -- only a probability.
"""

from typing import Optional

from app.alerts.models import AlertType, Severity
from app.alerts.schemas import AlertCreate

ALERT_MIN_MALWARE_PROBABILITY = 0.5

# Ordered high -> low; first threshold that risk_score meets or exceeds wins.
ALERT_SEVERITY_THRESHOLDS = [
    (90, Severity.CRITICAL),
    (75, Severity.HIGH),
    (50, Severity.MEDIUM),
    (0, Severity.LOW),
]


def is_alertable(malware_probability: Optional[float]) -> bool:
    """False only when a probability is given AND it's below the gate."""
    if malware_probability is None:
        return True
    return malware_probability >= ALERT_MIN_MALWARE_PROBABILITY


def map_risk_score_to_severity(risk_score: Optional[float]) -> Severity:
    if risk_score is None:
        return Severity.MEDIUM
    for threshold, severity in ALERT_SEVERITY_THRESHOLDS:
        if risk_score >= threshold:
            return severity
    return Severity.LOW


def build_alert_from_classification_event(
    detection_result: dict,
    *,
    recipient_user_email: Optional[str] = None,
) -> AlertCreate:
    """
    Translates the AI Classification module's confirmed detection payload
    into an AlertCreate. Raises ValueError if malware_probability is
    present and below ALERT_MIN_MALWARE_PROBABILITY (caller should check
    `is_alertable()` first, or catch this and skip alert creation).
    """
    malware_probability = detection_result.get("malware_probability")
    if not is_alertable(malware_probability):
        raise ValueError(
            f"malware_probability={malware_probability} is below the "
            f"alert threshold ({ALERT_MIN_MALWARE_PROBABILITY}); skipping."
        )

    risk_score = detection_result.get("risk_score")
    severity = map_risk_score_to_severity(risk_score)

    malware_family = detection_result.get("malware_family", "Unknown threat")
    file_id = detection_result.get("file_id", "unknown file")

    title = f"{malware_family} detected"
    message = (
        f"Classification flagged file '{file_id}' as '{malware_family}' "
        f"(risk score {risk_score}, probability {malware_probability})."
    )

    return AlertCreate(
        source_reference_id=detection_result.get("detection_id"),
        file_id=file_id,
        malware_family=malware_family,
        risk_score=risk_score,
        malware_probability=malware_probability,
        alert_type=AlertType.MALWARE_DETECTED,
        severity=severity,
        title=title,
        message=message,
        source=detection_result.get("source_module", "classification"),
        recipient_user_email=recipient_user_email,
    )
