import pytest

from app.models.alert import AlertSeverity, AlertStatus
from app.schemas.integration import ThreatDetectionResult
from app.services import alert_service


def make_detection(**overrides) -> ThreatDetectionResult:
    base = dict(
        detection_id="det-001",
        file_id="file-001",
        malware_family="Trojan",
        risk_score=82.0,
        confidence_score=0.91,
        source_module="classification",
    )
    base.update(overrides)
    return ThreatDetectionResult(**base)


# ---- Normal cases ----

def test_create_alert_from_high_risk_detection(db_session):
    detection = make_detection(risk_score=82.0)
    alert = alert_service.create_alert_from_detection(db_session, detection)

    assert alert.severity == AlertSeverity.HIGH
    assert alert.recipient_role == "security_analyst"
    assert alert.status == AlertStatus.NEW
    assert alert.notified is True
    assert alert.notification_channel == "console"


def test_create_alert_low_risk_routes_to_soc(db_session):
    detection = make_detection(detection_id="det-002", risk_score=20.0)
    alert = alert_service.create_alert_from_detection(db_session, detection)

    assert alert.severity == AlertSeverity.LOW
    assert alert.recipient_role == "soc_team"


def test_list_alerts_filters_by_severity(db_session):
    alert_service.create_alert_from_detection(db_session, make_detection(detection_id="a", risk_score=95))
    alert_service.create_alert_from_detection(db_session, make_detection(detection_id="b", risk_score=10))

    critical_only = alert_service.list_alerts(db_session, severity_filter=AlertSeverity.CRITICAL)
    assert len(critical_only) == 1
    assert critical_only[0].detection_id == "a"


def test_update_alert_status_sets_resolved_at(db_session):
    alert = alert_service.create_alert_from_detection(db_session, make_detection())
    updated = alert_service.update_alert_status(db_session, alert.id, AlertStatus.RESOLVED)

    assert updated.status == AlertStatus.RESOLVED
    assert updated.resolved_at is not None


# ---- Edge cases ----

def test_duplicate_detection_id_does_not_create_second_alert(db_session):
    detection = make_detection(detection_id="dup-1")
    first = alert_service.create_alert_from_detection(db_session, detection)
    second = alert_service.create_alert_from_detection(db_session, detection)

    assert first.id == second.id
    all_alerts = alert_service.list_alerts(db_session)
    assert len(all_alerts) == 1


def test_missing_optional_fields_still_creates_alert(db_session):
    detection = ThreatDetectionResult(
        detection_id="minimal-1",
        risk_score=55.0,
    )
    alert = alert_service.create_alert_from_detection(db_session, detection)
    assert alert.malware_family is None
    assert alert.severity == AlertSeverity.MEDIUM


def test_invalid_risk_score_rejected():
    with pytest.raises(Exception):
        ThreatDetectionResult(detection_id="bad-1", risk_score=150.0)


def test_update_status_on_nonexistent_alert_returns_none(db_session):
    result = alert_service.update_alert_status(db_session, "does-not-exist", AlertStatus.RESOLVED)
    assert result is None


# ---- Failure cases ----

def test_get_alert_nonexistent_returns_none(db_session):
    assert alert_service.get_alert(db_session, "nope") is None
