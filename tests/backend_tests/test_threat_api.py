"""
Integration tests for the Threat Monitoring REST API.

Tests all API endpoints using FastAPI's TestClient against an in-memory
SQLite database.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base, get_db
from app.modules.threat_monitoring.models import ThreatLog, ThreatTimelineEvent  # noqa: register models

# Override database before importing app
TEST_DATABASE_URL = "sqlite:///./test_threat_api.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


# Import app AFTER setting up the test database
from app.main import app

app.dependency_overrides[get_db] = override_get_db


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_threat_api.db"):
        try:
            os.remove("./test_threat_api.db")
        except OSError:
            pass


# =====================================================================
# HELPER
# =====================================================================

def _create_detection(**kwargs):
    """Helper to create a detection via the API."""
    defaults = {
        "filename": "test_file.exe",
        "prediction": "Trojan",
        "confidence": 85.0,
        "file_hash_sha256": "a" * 64,
        "file_type": "exe",
    }
    defaults.update(kwargs)
    return client.post("/api/v1/threats/detect", json=defaults)


# =====================================================================
# DETECTION ENDPOINT TESTS
# =====================================================================

class TestDetectionAPI:
    """Tests for POST /api/v1/threats/detect."""

    def test_record_detection_success(self):
        """Successfully record a malware detection."""
        response = _create_detection()
        assert response.status_code == 201

        data = response.json()
        assert data["message"] == "Detection recorded successfully."
        assert data["filename"] == "test_file.exe"
        assert data["prediction"] == "Trojan"
        assert data["risk_score"] > 0
        assert data["threat_id"] is not None

    def test_record_benign_detection(self):
        """Benign detections are auto-resolved."""
        response = _create_detection(prediction="Benign", confidence=95.0)
        assert response.status_code == 201

        data = response.json()
        assert data["risk_score"] == 0
        assert data["status"] == "resolved"

    def test_record_detection_validation_error(self):
        """Invalid payload returns 422."""
        response = client.post(
            "/api/v1/threats/detect",
            json={
                "filename": "",  # empty — should fail min_length=1
                "prediction": "Trojan",
                "confidence": 85.0,
            },
        )
        assert response.status_code == 422

    def test_confidence_out_of_range(self):
        """Confidence > 100 returns validation error."""
        response = _create_detection(confidence=150.0)
        assert response.status_code == 422

    def test_record_with_yara_matches(self):
        """Detection with YARA matches is recorded successfully."""
        response = _create_detection(
            yara_matches=["MALWARE_Trojan_Gen", "SUSPICIOUS_PowerShell"],
        )
        assert response.status_code == 201
        data = response.json()
        # YARA matches should increase the risk score
        assert data["risk_score"] > 0


# =====================================================================
# QUERY ENDPOINT TESTS
# =====================================================================

class TestQueryAPI:
    """Tests for GET /api/v1/threats and GET /api/v1/threats/{id}."""

    def test_list_threats_empty(self):
        """Empty database returns empty paginated response."""
        response = client.get("/api/v1/threats")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_threats_with_data(self):
        """List threats returns all recorded detections."""
        _create_detection(filename="file1.exe")
        _create_detection(filename="file2.exe")
        _create_detection(filename="file3.exe")

        response = client.get("/api/v1/threats")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    def test_list_threats_pagination(self):
        """Pagination works correctly."""
        for i in range(15):
            _create_detection(filename=f"file_{i}.exe")

        response = client.get("/api/v1/threats?page=1&page_size=5")
        data = response.json()
        assert data["total"] == 15
        assert len(data["items"]) == 5
        assert data["total_pages"] == 3

    def test_list_threats_filter_by_prediction(self):
        """Can filter by malware family."""
        _create_detection(prediction="Trojan")
        _create_detection(prediction="Ransomware")
        _create_detection(prediction="Benign")

        response = client.get("/api/v1/threats?prediction=Trojan")
        data = response.json()
        assert data["total"] == 1

    def test_list_threats_search(self):
        """Search by filename works."""
        _create_detection(filename="invoice.exe")
        _create_detection(filename="report.pdf")

        response = client.get("/api/v1/threats?search=invoice")
        data = response.json()
        assert data["total"] == 1

    def test_get_threat_detail(self):
        """Get single threat with timeline."""
        create_response = _create_detection()
        threat_id = create_response.json()["threat_id"]

        response = client.get(f"/api/v1/threats/{threat_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == threat_id
        assert data["filename"] == "test_file.exe"
        assert data["timeline"] is not None

    def test_get_threat_not_found(self):
        """Non-existent threat returns 404."""
        response = client.get("/api/v1/threats/nonexistent-id")
        assert response.status_code == 404


# =====================================================================
# STATUS UPDATE TESTS
# =====================================================================

class TestStatusAPI:
    """Tests for PATCH /api/v1/threats/{id}/status and /resolve."""

    def test_update_status(self):
        """Can update a threat's status."""
        create_response = _create_detection()
        threat_id = create_response.json()["threat_id"]

        response = client.patch(
            f"/api/v1/threats/{threat_id}/status",
            json={"status": "under_investigation"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "under_investigation"

    def test_resolve_threat(self):
        """Can resolve a threat."""
        create_response = _create_detection()
        threat_id = create_response.json()["threat_id"]

        response = client.patch(f"/api/v1/threats/{threat_id}/resolve")
        assert response.status_code == 200
        assert response.json()["status"] == "resolved"

    def test_update_nonexistent_threat(self):
        """Updating nonexistent threat returns 404."""
        response = client.patch(
            "/api/v1/threats/nonexistent/status",
            json={"status": "resolved"},
        )
        assert response.status_code == 404


# =====================================================================
# DELETE TESTS
# =====================================================================

class TestDeleteAPI:
    """Tests for DELETE /api/v1/threats/{id}."""

    def test_delete_threat(self):
        """Can delete a threat."""
        create_response = _create_detection()
        threat_id = create_response.json()["threat_id"]

        response = client.delete(f"/api/v1/threats/{threat_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/v1/threats/{threat_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent(self):
        """Deleting nonexistent threat returns 404."""
        response = client.delete("/api/v1/threats/nonexistent")
        assert response.status_code == 404


# =====================================================================
# DASHBOARD ENDPOINT TESTS
# =====================================================================

class TestDashboardAPI:
    """Tests for dashboard endpoints."""

    def test_dashboard_summary(self):
        """Dashboard summary returns aggregate statistics."""
        _create_detection(prediction="Trojan", confidence=90.0)
        _create_detection(prediction="Benign", confidence=95.0)

        response = client.get("/api/v1/threats/dashboard/summary")
        assert response.status_code == 200

        data = response.json()
        assert data["total_files"] == 2
        assert data["malware_files"] == 1
        assert data["benign_files"] == 1

    def test_dashboard_trends(self):
        """Trends endpoint returns time-series data."""
        _create_detection()

        response = client.get("/api/v1/threats/dashboard/trends?days=7")
        assert response.status_code == 200

        data = response.json()
        assert data["days"] == 7
        assert len(data["data"]) == 7

    def test_dashboard_families(self):
        """Family breakdown returns grouped data."""
        _create_detection(prediction="Trojan")
        _create_detection(prediction="Trojan")
        _create_detection(prediction="Ransomware")

        response = client.get("/api/v1/threats/dashboard/families")
        assert response.status_code == 200

        data = response.json()
        assert data["total_malware"] == 3
        assert len(data["families"]) == 2


# =====================================================================
# REPORT ENDPOINT TESTS
# =====================================================================

class TestReportAPI:
    """Tests for report generation."""

    def test_generate_report(self):
        """Report generation returns comprehensive data."""
        _create_detection(prediction="Trojan", confidence=90.0)
        _create_detection(prediction="Ransomware", confidence=85.0)

        response = client.get("/api/v1/threats/reports/generate?days=30")
        assert response.status_code == 200

        data = response.json()
        assert "generated_at" in data
        assert "summary" in data
        assert "trends" in data
        assert "family_breakdown" in data
        assert "status_distribution" in data


# =====================================================================
# TIMELINE ENDPOINT TESTS
# =====================================================================

class TestTimelineAPI:
    """Tests for timeline endpoints."""

    def test_get_timeline(self):
        """Can get a threat's timeline."""
        create_response = _create_detection()
        threat_id = create_response.json()["threat_id"]

        response = client.get(f"/api/v1/threats/timeline/{threat_id}")
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 1  # at least the "detected" event

    def test_timeline_grows_with_status_changes(self):
        """Timeline grows when status is updated."""
        create_response = _create_detection()
        threat_id = create_response.json()["threat_id"]

        # Update status
        client.patch(
            f"/api/v1/threats/{threat_id}/status",
            json={"status": "under_investigation"},
        )

        response = client.get(f"/api/v1/threats/timeline/{threat_id}")
        data = response.json()
        assert len(data) >= 2  # detected + status_changed


# =====================================================================
# MALWARE TRACKING TESTS
# =====================================================================

class TestTrackingAPI:
    """Tests for malware tracking by hash."""

    def test_track_by_hash(self):
        """Can track a file across detections using hash."""
        hash_val = "c" * 64
        _create_detection(file_hash_sha256=hash_val, filename="file1.exe")
        _create_detection(file_hash_sha256=hash_val, filename="file2.exe")
        _create_detection(file_hash_sha256="d" * 64, filename="file3.exe")

        response = client.get(f"/api/v1/threats/track/{hash_val}")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2


# =====================================================================
# MONGODB LOGS TESTS
# =====================================================================

class TestMongoLogsAPI:
    """Tests for MongoDB detection log endpoints."""

    def test_list_logs_without_mongo(self):
        """Logs endpoint works even without MongoDB (returns empty)."""
        response = client.get("/api/v1/threats/logs")
        assert response.status_code == 200

        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []


# =====================================================================
# HEALTH CHECK TESTS
# =====================================================================

class TestHealthCheck:
    """Tests for health check endpoints."""

    def test_root_endpoint(self):
        """Root endpoint returns service info."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "ThreatLens Backend Running"
        assert "threat_monitoring" in data.get("modules", {})

    def test_health_endpoint(self):
        """Health check returns status."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
