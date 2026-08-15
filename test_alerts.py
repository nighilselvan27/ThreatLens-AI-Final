"""
Test suite for the Alert & Notification Module (Member 6).

Run from the `backend/` directory so the `app` package resolves:
    cd backend
    pip install -r ../requirements.txt pytest httpx python-multipart
    DATABASE_URL=sqlite:///./test.db ALERT_INGEST_API_KEY=test-key \
        pytest ../tests/backend_tests/test_alerts.py -v

Uses a throwaway SQLite file DB via the DATABASE_URL env var so tests
don't require a running PostgreSQL instance. CI/Member 8 can point this
at a real Postgres instance by setting DATABASE_URL instead.
"""

import os
import sys
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_alerts.db")
os.environ.setdefault("ALERT_INGEST_API_KEY", "test-key")

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from app.alerts.database import Base, engine
from app.alerts.adapters import build_alert_from_threat_event, is_benign

client = TestClient(app)

INTERNAL_HEADERS = {"X-Internal-Api-Key": "test-key"}


def _token(role: str, user_id: str = "user-1") -> dict:
    t = jwt.encode({"sub": user_id, "role": role}, "change-me", algorithm="HS256")
    return {"Authorization": f"Bearer {t}"}


ANALYST = _token("security_analyst", "analyst-1")
SOC = _token("soc_team_member", "soc-1")
ADMIN = _token("administrator", "admin-1")
RESEARCHER = _token("researcher", "researcher-1")


@pytest.fixture(autouse=True)
def _clean_db():
    """Reset the alerts table before every test for isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def _sample_detection(**overrides) -> dict:
    detection = {
        "filename": "invoice.exe",
        "prediction": "Trojan",
        "confidence": 92,
        "risk_score": 95,
        "risk_level": "High Risk",
        "file_hash": "sha256-abc123",
    }
    detection.update(overrides)
    return detection


def _ingest(detection=None) -> dict:
    detection = detection or _sample_detection()
    payload = build_alert_from_threat_event(detection)
    r = client.post("/api/v1/alerts/ingest", json=payload.model_dump(mode="json"), headers=INTERNAL_HEADERS)
    assert r.status_code == 201, r.text
    return r.json()


# 1. Alert creation
def test_create_alert_via_ingest():
    alert = _ingest()
    assert alert["title"].startswith("Trojan detected")
    assert alert["severity"] == "critical"
    assert alert["status"] == "detected"
    assert alert["isRead"] is False


# 2. Alert retrieval (list)
def test_list_alerts():
    _ingest()
    r = client.get("/api/v1/alerts", headers=ANALYST)
    assert r.status_code == 200
    assert len(r.json()) == 1


# 3. Alert retrieval by ID
def test_get_alert_by_id():
    created = _ingest()
    r = client.get(f"/api/v1/alerts/{created['id']}", headers=ANALYST)
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


# 4. Mark as read
def test_mark_as_read():
    created = _ingest()
    r = client.patch(f"/api/v1/alerts/{created['id']}/read", headers=SOC)
    assert r.status_code == 200
    assert r.json()["isRead"] is True


# 5. Status update
def test_update_status():
    created = _ingest()
    r = client.patch(
        f"/api/v1/alerts/{created['id']}/status",
        json={"status": "under_investigation"},
        headers=ANALYST,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "under_investigation"


# 6. Alert resolution
def test_resolve_alert():
    created = _ingest()
    r = client.patch(f"/api/v1/alerts/{created['id']}/resolve", headers=ANALYST)
    assert r.status_code == 200
    assert r.json()["status"] == "resolved"
    assert r.json()["resolvedAt"] is not None


# 7. Unauthorized access
def test_list_requires_auth():
    r = client.get("/api/v1/alerts")
    assert r.status_code == 401


def test_soc_cannot_resolve():
    created = _ingest()
    r = client.patch(f"/api/v1/alerts/{created['id']}/resolve", headers=SOC)
    assert r.status_code == 403


def test_ingest_requires_valid_internal_key():
    payload = build_alert_from_threat_event(_sample_detection())
    r = client.post(
        "/api/v1/alerts/ingest",
        json=payload.model_dump(mode="json"),
        headers={"X-Internal-Api-Key": "wrong-key"},
    )
    assert r.status_code == 401


# 8. Invalid alert ID
def test_get_nonexistent_alert_returns_404():
    r = client.get(f"/api/v1/alerts/{uuid.uuid4()}", headers=ANALYST)
    assert r.status_code == 404


def test_update_status_nonexistent_alert_returns_404():
    r = client.patch(
        f"/api/v1/alerts/{uuid.uuid4()}/status",
        json={"status": "resolved"},
        headers=ANALYST,
    )
    assert r.status_code == 404


# 9. Invalid severity/status
def test_invalid_status_value_rejected():
    created = _ingest()
    r = client.patch(
        f"/api/v1/alerts/{created['id']}/status",
        json={"status": "not_a_real_status"},
        headers=ANALYST,
    )
    assert r.status_code == 422


def test_invalid_severity_filter_rejected():
    r = client.get("/api/v1/alerts?severity=not_a_real_severity", headers=ANALYST)
    assert r.status_code == 422


# 10. Duplicate alert prevention
def test_duplicate_detection_does_not_create_second_alert():
    first = _ingest()
    second = _ingest()  # identical detection payload
    assert first["id"] == second["id"]
    r = client.get("/api/v1/alerts", headers=ANALYST)
    assert len(r.json()) == 1


def test_different_file_hash_creates_new_alert():
    _ingest(_sample_detection(file_hash="sha256-aaa"))
    _ingest(_sample_detection(file_hash="sha256-bbb"))
    r = client.get("/api/v1/alerts", headers=ANALYST)
    assert len(r.json()) == 2


# 11. Threat event -> alert generation (adapter)
def test_benign_detection_is_not_alertable():
    assert is_benign("Benign") is True
    with pytest.raises(ValueError):
        build_alert_from_threat_event(_sample_detection(prediction="Benign"))


@pytest.mark.parametrize(
    "risk_level,expected_severity",
    [
        ("High Risk", "critical"),
        ("Medium Risk", "high"),
        ("Low Risk", "medium"),
        ("Minimal Risk", "low"),
    ],
)
def test_risk_level_severity_mapping(risk_level, expected_severity):
    payload = build_alert_from_threat_event(_sample_detection(risk_level=risk_level))
    assert payload.severity.value == expected_severity


# 12. Role-based access
def test_researcher_only_sees_own_alerts():
    payload = build_alert_from_threat_event(_sample_detection(), recipient_user_id="researcher-1")
    client.post("/api/v1/alerts/ingest", json=payload.model_dump(mode="json"), headers=INTERNAL_HEADERS)
    payload2 = build_alert_from_threat_event(_sample_detection(file_hash="sha256-other"))  # no recipient
    client.post("/api/v1/alerts/ingest", json=payload2.model_dump(mode="json"), headers=INTERNAL_HEADERS)

    r = client.get("/api/v1/alerts", headers=RESEARCHER)
    assert len(r.json()) == 1  # only the one addressed to them


def test_admin_can_delete_analyst_cannot():
    created = _ingest()
    r = client.delete(f"/api/v1/alerts/{created['id']}", headers=ANALYST)
    assert r.status_code == 403

    r2 = client.delete(f"/api/v1/alerts/{created['id']}", headers=ADMIN)
    assert r2.status_code == 204


def test_stats_summary():
    _ingest()
    r = client.get("/api/v1/alerts/stats/summary", headers=SOC)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["critical"] == 1
