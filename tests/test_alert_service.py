import pytest
import uuid

from app.alerts.adapters import build_alert_from_classification_event, is_alertable
from app.alerts.models import AlertStatus, Severity
from app.alerts.service import (
    create_alert,
    get_alert,
    list_alerts,
    mark_as_read,
    resolve_alert,
    update_status,
)
from app.alerts.schemas import AlertCreate


def make_detection(**overrides):
    data = {
        "detection_id": "det-001",
        "risk_score": 82.0,
        "file_id": "file-001",
        "malware_family": "Trojan",
        "malware_probability": 0.91,
        "source_module": "classification",
    }
    data.update(overrides)
    return data


def make_payload(**overrides):
    detection = make_detection(**overrides)
    return build_alert_from_classification_event(detection)


def test_create_alert_from_classification_event(db_session):
    payload = make_payload(risk_score=82.0)
    alert, created = create_alert(db_session, payload)

    assert created is True
    assert alert.severity == Severity.HIGH
    assert alert.status == AlertStatus.DETECTED
    assert alert.source_reference_id == "det-001"
    assert alert.malware_probability == 0.91


def test_low_probability_detection_is_not_alertable():
    assert is_alertable(0.1) is False

    with pytest.raises(ValueError):
        build_alert_from_classification_event(
            make_detection(malware_probability=0.1)
        )


@pytest.mark.parametrize(
    "risk_score,expected_severity",
    [
        (95, Severity.CRITICAL),
        (80, Severity.HIGH),
        (60, Severity.MEDIUM),
        (20, Severity.LOW),
    ],
)
def test_risk_score_severity_mapping(risk_score, expected_severity):
    payload = make_payload(risk_score=risk_score)
    assert payload.severity == expected_severity


def test_duplicate_detection_id_does_not_create_second_alert(db_session):
    payload = make_payload()

    first, created_first = create_alert(db_session, payload)
    second, created_second = create_alert(db_session, payload)

    assert created_first is True
    assert created_second is False
    assert first.id == second.id
    assert len(list_alerts(
        db_session,
        requester_role="Security Analyst",
        requester_email="analyst@example.com",
    )) == 1


def test_get_alert(db_session):
    payload = make_payload()
    alert, _ = create_alert(db_session, payload)

    found = get_alert(db_session, alert.id)

    assert found is not None
    assert found.id == alert.id


def test_get_missing_alert_returns_none(db_session):
    assert get_alert(db_session, uuid.uuid4()) is None


def test_mark_as_read(db_session):
    payload = make_payload()
    alert, _ = create_alert(db_session, payload)

    updated = mark_as_read(db_session, alert.id)

    assert updated is not None
    assert updated.is_read is True


def test_update_status(db_session):
    payload = make_payload()
    alert, _ = create_alert(db_session, payload)

    updated = update_status(
        db_session,
        alert.id,
        AlertStatus.UNDER_INVESTIGATION,
    )

    assert updated.status == AlertStatus.UNDER_INVESTIGATION


def test_resolve_alert_sets_resolved_at(db_session):
    payload = make_payload()
    alert, _ = create_alert(db_session, payload)

    resolved = resolve_alert(db_session, alert.id)

    assert resolved.status == AlertStatus.RESOLVED
    assert resolved.resolved_at is not None


def test_list_alerts_filters_by_severity(db_session):
    create_alert(db_session, make_payload(
        detection_id="critical-1",
        risk_score=95,
    ))
    create_alert(db_session, make_payload(
        detection_id="low-1",
        risk_score=20,
    ))

    critical_only = list_alerts(
        db_session,
        requester_role="Security Analyst",
        requester_email="analyst@example.com",
        severity=Severity.CRITICAL,
    )

    assert len(critical_only) == 1
    assert critical_only[0].source_reference_id == "critical-1"


def test_unread_filter(db_session):
    alert, _ = create_alert(db_session, make_payload())

    unread = list_alerts(
        db_session,
        requester_role="Security Analyst",
        requester_email="analyst@example.com",
        unread_only=True,
    )

    assert len(unread) == 1

    mark_as_read(db_session, alert.id)

    unread_after_read = list_alerts(
        db_session,
        requester_role="Security Analyst",
        requester_email="analyst@example.com",
        unread_only=True,
    )

    assert len(unread_after_read) == 0


def test_invalid_risk_score_rejected():
    with pytest.raises(Exception):
        AlertCreate(
            title="Invalid alert",
            message="Invalid risk score",
            risk_score=150,
        )
