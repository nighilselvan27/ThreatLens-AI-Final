"""
Adapter: Threat Monitoring (Member 5) -> Alert & Notification (Member 6).

WHY THIS EXISTS
Member 5's module (backend/app/modules/Service.py, report.py,
risk_score.py) is not currently runnable: `ThreatMonitoringService`
imports `app.modules.threat_monitoring.models.ThreatLog` and
`app.modules.threat_monitoring.repository.ThreatRepository`, but
`backend/app/modules/threat_monitoring` exists only as an empty file,
not a package -- those classes don't exist anywhere in the repo yet.

Rather than build Member 5's module for them (out of scope, and risks
guessing an incompatible design), this file documents and implements
the *translation* from the one real contract that does exist --
`ThreatMonitoringService.save_detection()`'s return shape -- into an
`AlertCreate`. Once Member 5's module is finished, wire it up in ONE
of these two ways:

  Option A (same-process, recommended): after their save_detection()
  call succeeds, have it call this function directly and pass the
  result into `app.alerts.service.create_alert(db, alert_payload)`.
  This avoids an HTTP round-trip and keeps both operations in the same
  DB transaction if desired.

      from app.alerts.adapters import build_alert_from_threat_event
      from app.alerts.service import create_alert as create_alert_record

      detection_result = ThreatMonitoringService.save_detection(...)
      if detection_result["prediction"].lower() != "benign":
          alert_payload = build_alert_from_threat_event(detection_result)
          create_alert_record(alerts_db_session, alert_payload)

  Option B (HTTP, if Member 5's module runs as a separate service):
  POST the same `detection_result` dict to
  `POST /api/v1/alerts/ingest` with header
  `X-Internal-Api-Key: <ALERT_INGEST_API_KEY>`. The router accepts the
  raw AlertCreate-shaped body; convert with this same function first,
  since the endpoint expects AlertCreate fields, not the raw
  Member 5 dict.

CONTRACT (Member 5's actual return shape, from Service.py today):
    {
        "message": str,
        "filename": str,
        "prediction": str,       # e.g. "Trojan", "Ransomware", "Benign"
        "confidence": float,     # 0-100
        "risk_score": int,       # 95 / 80 / 60 / 30, from risk_score.py
        "risk_level": str,       # "High Risk" / "Medium Risk" / "Low Risk" / "Minimal Risk"
    }
Optionally, if Member 5 adds these fields later, they will be picked up
automatically: "file_hash" (sha256), "detection_id" / "scan_id" (for
exact-match dedup -- see service.py), "recipient_user_id".

SEVERITY MAPPING (documented assumption -- neither the PDF nor the repo
defines a canonical mapping between Member 5's 4-level risk_level and
this module's 5-level Severity):
    "High Risk"    (confidence >= 90) -> CRITICAL
    "Medium Risk"  (confidence >= 75) -> HIGH
    "Low Risk"     (confidence >= 50) -> MEDIUM
    "Minimal Risk" (confidence <  50) -> LOW
Severity.INFO is never produced by this adapter; it's reserved for
non-detection system notices (e.g. "YARA rule updated") that a future
module might raise directly via POST /api/v1/alerts.
"""

from typing import Optional

from app.alerts.models import AlertType, Severity
from app.alerts.schemas import AlertCreate

_RISK_LEVEL_TO_SEVERITY = {
    "high risk": Severity.CRITICAL,
    "medium risk": Severity.HIGH,
    "low risk": Severity.MEDIUM,
    "minimal risk": Severity.LOW,
}

_BENIGN_PREDICTIONS = {"benign", "clean", "safe", "not malicious"}


def is_benign(prediction: str) -> bool:
    return (prediction or "").strip().lower() in _BENIGN_PREDICTIONS


def map_risk_level_to_severity(risk_level: str) -> Severity:
    return _RISK_LEVEL_TO_SEVERITY.get((risk_level or "").strip().lower(), Severity.MEDIUM)


def build_alert_from_threat_event(
    detection_result: dict,
    *,
    recipient_user_id: Optional[str] = None,
    recipient_email: Optional[str] = None,
) -> AlertCreate:
    """
    Translates Member 5's detection result dict into an AlertCreate.
    Raises ValueError if the event is benign (callers should check
    `is_benign()` first, or catch this and skip alert creation).
    """
    prediction = detection_result.get("prediction", "Unknown")
    if is_benign(prediction):
        raise ValueError("Refusing to build an alert for a benign detection result.")

    risk_level = detection_result.get("risk_level", "")
    severity = map_risk_level_to_severity(risk_level)

    filename = detection_result.get("filename", "unknown file")
    confidence = detection_result.get("confidence")

    title = f"{prediction} detected: {filename}"
    message = (
        f"The classification engine flagged '{filename}' as '{prediction}' "
        f"with {confidence}% confidence ({risk_level or 'unrated'})."
    )

    return AlertCreate(
        source_reference_id=detection_result.get("detection_id") or detection_result.get("scan_id"),
        file_name=filename,
        file_hash_sha256=detection_result.get("file_hash"),
        malware_family=prediction,
        risk_score=detection_result.get("risk_score"),
        alert_type=AlertType.MALWARE_DETECTED,
        severity=severity,
        title=title,
        message=message,
        source="Threat Monitoring",
        recipient_user_id=recipient_user_id,
        recipient_email=recipient_email,
    )
