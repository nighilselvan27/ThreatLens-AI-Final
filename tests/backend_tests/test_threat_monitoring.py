"""
Unit tests for the Threat Monitoring module.

Tests cover:
    - Risk score calculation (multi-factor)
    - Detection recording workflow
    - Threat queries and filters
    - Status transitions
    - Timeline event generation
    - Dashboard aggregation
    - Report generation
"""

import os
import sys
import uuid
import pytest
from datetime import datetime, timezone

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.database import Base
from app.modules.threat_monitoring.models import (
    ThreatLog,
    ThreatTimelineEvent,
    ThreatStatus,
    RiskLevel,
    TimelineEventType,
)
from app.modules.threat_monitoring.schemas import ThreatLogCreate
from app.modules.threat_monitoring.risk_score import (
    calculate_risk_score,
    get_recommended_action,
)
from app.modules.threat_monitoring.repository import ThreatRepository
from app.modules.threat_monitoring.service import ThreatMonitoringService


# ---------------------------------------------------------------------------
# Test database fixture (in-memory SQLite)
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite:///./test_threat_monitoring.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Clean up test database file
    if os.path.exists("./test_threat_monitoring.db"):
        try:
            os.remove("./test_threat_monitoring.db")
        except OSError:
            pass


@pytest.fixture
def db():
    """Provide a clean database session for each test."""
    session = TestSession()
    try:
        yield session
    finally:
        session.close()


# =====================================================================
# RISK SCORE TESTS
# =====================================================================

class TestRiskScore:
    """Tests for the multi-factor risk score calculator."""

    def test_benign_prediction_returns_zero(self):
        """Benign predictions should always return score 0 / minimal."""
        score, level = calculate_risk_score(95.0, prediction="Benign")
        assert score == 0
        assert level == "minimal"

    def test_benign_case_insensitive(self):
        """Benign detection is case-insensitive."""
        for pred in ["benign", "BENIGN", "Clean", "safe", "Not Malicious"]:
            score, level = calculate_risk_score(99.0, prediction=pred)
            assert score == 0
            assert level == "minimal"

    def test_high_confidence_trojan(self):
        """High confidence Trojan should yield high/critical risk."""
        score, level = calculate_risk_score(90.0, prediction="Trojan")
        assert score >= 70  # 90*0.7 + 10 (trojan bonus) = 73
        assert level in ("high", "critical")

    def test_ransomware_gets_highest_bonus(self):
        """Ransomware has the highest family severity bonus."""
        score_ransom, _ = calculate_risk_score(80.0, prediction="Ransomware")
        score_adware, _ = calculate_risk_score(80.0, prediction="Adware")
        assert score_ransom > score_adware

    def test_yara_matches_increase_score(self):
        """YARA matches should add +2 per match (max +10)."""
        score_no_yara, _ = calculate_risk_score(60.0, prediction="Trojan")
        score_with_yara, _ = calculate_risk_score(
            60.0,
            prediction="Trojan",
            yara_matches=["RULE_1", "RULE_2", "RULE_3"],
        )
        assert score_with_yara > score_no_yara
        assert score_with_yara - score_no_yara == 6  # 3 * 2

    def test_yara_bonus_capped_at_10(self):
        """YARA bonus should cap at +10 even with many matches."""
        score, _ = calculate_risk_score(
            50.0,
            prediction="Unknown",
            yara_matches=["R1", "R2", "R3", "R4", "R5", "R6", "R7"],
        )
        # 50*0.7 + 5 (unknown) + 10 (capped) = 50
        assert score <= 100

    def test_suspicious_indicators_increase_score(self):
        """Suspicious indicators should add +2 per category (max +8)."""
        score_no_ind, _ = calculate_risk_score(60.0, prediction="Trojan")
        score_with_ind, _ = calculate_risk_score(
            60.0,
            prediction="Trojan",
            suspicious_indicators={"urls": ["bad.com"], "ips": ["1.2.3.4"]},
        )
        assert score_with_ind > score_no_ind

    def test_score_never_exceeds_100(self):
        """Score should be capped at 100."""
        score, _ = calculate_risk_score(
            100.0,
            prediction="Ransomware",
            yara_matches=["R1", "R2", "R3", "R4", "R5"],
            suspicious_indicators={"a": 1, "b": 2, "c": 3, "d": 4},
        )
        assert score <= 100

    def test_score_never_below_zero(self):
        """Score should never go below 0."""
        score, _ = calculate_risk_score(0.0, prediction="Unknown")
        assert score >= 0

    def test_confidence_out_of_range_raises(self):
        """Confidence outside 0-100 should raise ValueError."""
        with pytest.raises(ValueError):
            calculate_risk_score(-1.0)
        with pytest.raises(ValueError):
            calculate_risk_score(101.0)

    def test_risk_levels_are_correct(self):
        """Verify the threshold-to-level mapping."""
        # 100*0.7 + 15 (ransomware) = 85 → critical
        _, level = calculate_risk_score(100.0, prediction="Ransomware")
        assert level == "critical"

        _, level = calculate_risk_score(0.0, prediction="Unknown")
        assert level == "minimal"

    def test_recommended_action_generation(self):
        """Test recommended action text generation."""
        action = get_recommended_action("critical", "Ransomware")
        assert "IMMEDIATE" in action
        assert "Ransomware" in action

        action = get_recommended_action("minimal", "Benign")
        assert "No immediate" in action


# =====================================================================
# REPOSITORY TESTS
# =====================================================================

class TestThreatRepository:
    """Tests for the PostgreSQL data access layer."""

    def _create_sample_threat(self, db, **kwargs):
        """Helper to create and save a sample threat."""
        defaults = {
            "id": str(uuid.uuid4()),
            "filename": "test_file.exe",
            "prediction": "Trojan",
            "confidence": 85.0,
            "risk_score": 75,
            "risk_level": RiskLevel.HIGH,
            "status": ThreatStatus.DETECTED,
        }
        defaults.update(kwargs)
        threat = ThreatLog(**defaults)
        return ThreatRepository.save_threat(db, threat)

    def test_save_and_retrieve_threat(self, db):
        """Can save and retrieve a threat by ID."""
        saved = self._create_sample_threat(db)
        retrieved = ThreatRepository.get_threat_by_id(db, saved.id)
        assert retrieved is not None
        assert retrieved.filename == "test_file.exe"
        assert retrieved.prediction == "Trojan"

    def test_get_all_threats_pagination(self, db):
        """Pagination works correctly."""
        for i in range(25):
            self._create_sample_threat(db, filename=f"file_{i}.exe")

        items, total = ThreatRepository.get_all_threats(db, page=1, page_size=10)
        assert total == 25
        assert len(items) == 10

        items2, total2 = ThreatRepository.get_all_threats(db, page=3, page_size=10)
        assert total2 == 25
        assert len(items2) == 5  # 25 - 20 = 5 remaining

    def test_filter_by_prediction(self, db):
        """Can filter threats by prediction/malware family."""
        self._create_sample_threat(db, prediction="Trojan")
        self._create_sample_threat(db, prediction="Ransomware")
        self._create_sample_threat(db, prediction="Benign")

        items, total = ThreatRepository.get_all_threats(db, prediction="Trojan")
        assert total == 1
        assert items[0].prediction == "Trojan"

    def test_filter_by_status(self, db):
        """Can filter threats by status."""
        self._create_sample_threat(db, status=ThreatStatus.DETECTED)
        self._create_sample_threat(db, status=ThreatStatus.RESOLVED)

        items, total = ThreatRepository.get_all_threats(db, status="detected")
        assert total == 1

    def test_search_by_filename(self, db):
        """Can search threats by filename."""
        self._create_sample_threat(db, filename="invoice.exe")
        self._create_sample_threat(db, filename="report.pdf")

        items, total = ThreatRepository.get_all_threats(db, search="invoice")
        assert total == 1
        assert items[0].filename == "invoice.exe"

    def test_update_threat_status(self, db):
        """Can update a threat's status."""
        saved = self._create_sample_threat(db)
        updated = ThreatRepository.update_threat_status(
            db, saved.id, ThreatStatus.UNDER_INVESTIGATION
        )
        assert updated is not None
        assert updated.status == ThreatStatus.UNDER_INVESTIGATION

    def test_resolve_sets_resolved_at(self, db):
        """Resolving a threat sets the resolved_at timestamp."""
        saved = self._create_sample_threat(db)
        updated = ThreatRepository.update_threat_status(
            db, saved.id, ThreatStatus.RESOLVED
        )
        assert updated.resolved_at is not None

    def test_delete_threat(self, db):
        """Can delete a threat."""
        saved = self._create_sample_threat(db)
        result = ThreatRepository.delete_threat(db, saved.id)
        assert result is True
        assert ThreatRepository.get_threat_by_id(db, saved.id) is None

    def test_delete_nonexistent_returns_false(self, db):
        """Deleting a nonexistent threat returns False."""
        assert ThreatRepository.delete_threat(db, "nonexistent-id") is False

    def test_add_timeline_event(self, db):
        """Can add timeline events to a threat."""
        saved = self._create_sample_threat(db)
        event = ThreatRepository.add_timeline_event(
            db,
            threat_id=saved.id,
            event_type=TimelineEventType.DETECTED,
            description="Malware detected",
            created_by="system",
        )
        assert event.threat_id == saved.id
        assert event.event_type == TimelineEventType.DETECTED

    def test_get_threat_timeline(self, db):
        """Can retrieve timeline events for a threat."""
        saved = self._create_sample_threat(db)
        ThreatRepository.add_timeline_event(
            db, saved.id, TimelineEventType.DETECTED, "Detected"
        )
        ThreatRepository.add_timeline_event(
            db, saved.id, TimelineEventType.ANALYZED, "Analyzed"
        )

        events = ThreatRepository.get_threat_timeline(db, saved.id)
        assert len(events) == 2

    def test_count_methods(self, db):
        """Count methods return correct values."""
        self._create_sample_threat(db, prediction="Trojan")
        self._create_sample_threat(db, prediction="Ransomware")
        self._create_sample_threat(db, prediction="Benign")

        assert ThreatRepository.total_files(db) == 3
        assert ThreatRepository.get_malware_count(db) == 2
        assert ThreatRepository.get_benign_count(db) == 1

    def test_get_threats_by_hash(self, db):
        """Can find threats by SHA-256 hash."""
        hash_val = "abc123" * 10 + "abcd"  # 64 chars
        self._create_sample_threat(db, file_hash_sha256=hash_val)
        self._create_sample_threat(db, file_hash_sha256=hash_val)
        self._create_sample_threat(db, file_hash_sha256="different_hash")

        results = ThreatRepository.get_threats_by_hash(db, hash_val)
        assert len(results) == 2

    def test_get_threats_by_family(self, db):
        """Family breakdown returns correct grouping."""
        for _ in range(3):
            self._create_sample_threat(db, prediction="Trojan")
        for _ in range(2):
            self._create_sample_threat(db, prediction="Ransomware")

        families = ThreatRepository.get_threats_by_family(db)
        assert len(families) == 2
        assert families[0] == ("Trojan", 3)  # highest count first
        assert families[1] == ("Ransomware", 2)

    def test_status_distribution(self, db):
        """Status distribution returns correct counts."""
        self._create_sample_threat(db, status=ThreatStatus.DETECTED)
        self._create_sample_threat(db, status=ThreatStatus.DETECTED)
        self._create_sample_threat(db, status=ThreatStatus.RESOLVED)

        dist = ThreatRepository.get_status_distribution(db)
        assert dist.get("detected") == 2
        assert dist.get("resolved") == 1

    def test_active_and_resolved_counts(self, db):
        """Active and resolved count methods work."""
        self._create_sample_threat(db, status=ThreatStatus.DETECTED)
        self._create_sample_threat(db, status=ThreatStatus.UNDER_INVESTIGATION)
        self._create_sample_threat(db, status=ThreatStatus.RESOLVED)
        self._create_sample_threat(db, status=ThreatStatus.FALSE_POSITIVE)

        assert ThreatRepository.get_active_threat_count(db) == 2
        assert ThreatRepository.get_resolved_threat_count(db) == 2


# =====================================================================
# SERVICE TESTS
# =====================================================================

class TestThreatMonitoringService:
    """Tests for the business logic service layer."""

    def test_record_detection_malware(self, db):
        """Recording a malware detection stores it and returns enriched data."""
        payload = ThreatLogCreate(
            filename="malware.exe",
            prediction="Trojan",
            confidence=87.5,
            file_hash_sha256="a" * 64,
            file_type="exe",
        )
        result = ThreatMonitoringService.record_detection(db, payload)

        assert result["message"] == "Detection recorded successfully."
        assert result["filename"] == "malware.exe"
        assert result["prediction"] == "Trojan"
        assert result["risk_score"] > 0
        assert result["risk_level"] in ("critical", "high", "medium", "low", "minimal")
        assert result["status"] == "detected"
        assert result["threat_id"] is not None

    def test_record_detection_benign(self, db):
        """Benign detections are auto-resolved with minimal risk."""
        payload = ThreatLogCreate(
            filename="safe_file.pdf",
            prediction="Benign",
            confidence=95.0,
        )
        result = ThreatMonitoringService.record_detection(db, payload)

        assert result["risk_score"] == 0
        assert result["risk_level"] == "minimal"
        assert result["status"] == "resolved"  # auto-resolved
        assert result["alert_triggered"] is False

    def test_get_threat_detail(self, db):
        """Can retrieve a threat with timeline."""
        payload = ThreatLogCreate(
            filename="test.exe",
            prediction="Worm",
            confidence=70.0,
        )
        result = ThreatMonitoringService.record_detection(db, payload)

        detail = ThreatMonitoringService.get_threat_detail(db, result["threat_id"])
        assert detail is not None
        assert detail.filename == "test.exe"
        assert detail.timeline is not None
        assert len(detail.timeline) >= 1  # at least the "detected" event

    def test_get_threat_detail_not_found(self, db):
        """Non-existent threat returns None."""
        assert ThreatMonitoringService.get_threat_detail(db, "nonexistent") is None

    def test_get_threat_history_pagination(self, db):
        """Threat history is paginated correctly."""
        for i in range(15):
            ThreatMonitoringService.record_detection(
                db,
                ThreatLogCreate(
                    filename=f"file_{i}.exe",
                    prediction="Trojan",
                    confidence=75.0,
                ),
            )

        result = ThreatMonitoringService.get_threat_history(db, page=1, page_size=5)
        assert result.total == 15
        assert len(result.items) == 5
        assert result.total_pages == 3

    def test_update_threat_status(self, db):
        """Can update a threat's status."""
        payload = ThreatLogCreate(
            filename="test.exe",
            prediction="Trojan",
            confidence=80.0,
        )
        result = ThreatMonitoringService.record_detection(db, payload)

        updated = ThreatMonitoringService.update_threat_status(
            db, result["threat_id"], "under_investigation", "analyst_1"
        )
        assert updated is not None
        assert updated.status == "under_investigation"

    def test_resolve_threat(self, db):
        """Can resolve a threat."""
        payload = ThreatLogCreate(
            filename="test.exe",
            prediction="Trojan",
            confidence=80.0,
        )
        result = ThreatMonitoringService.record_detection(db, payload)

        resolved = ThreatMonitoringService.resolve_threat(
            db, result["threat_id"], "analyst_1"
        )
        assert resolved is not None
        assert resolved.status == "resolved"

    def test_track_malware_by_hash(self, db):
        """Can track a file across multiple detections by hash."""
        hash_val = "b" * 64
        for _ in range(3):
            ThreatMonitoringService.record_detection(
                db,
                ThreatLogCreate(
                    filename="suspicious.exe",
                    prediction="Trojan",
                    confidence=80.0,
                    file_hash_sha256=hash_val,
                ),
            )

        results = ThreatMonitoringService.track_malware(db, hash_val)
        assert len(results) == 3

    def test_get_threat_timeline(self, db):
        """Can get a threat's timeline."""
        payload = ThreatLogCreate(
            filename="test.exe",
            prediction="Trojan",
            confidence=80.0,
        )
        result = ThreatMonitoringService.record_detection(db, payload)

        # Update status to generate more timeline events
        ThreatMonitoringService.update_threat_status(
            db, result["threat_id"], "under_investigation"
        )

        timeline = ThreatMonitoringService.get_threat_timeline(db, result["threat_id"])
        assert timeline is not None
        assert len(timeline) >= 2  # detected + status_changed

    def test_dashboard_summary(self, db):
        """Dashboard summary aggregates correctly."""
        ThreatMonitoringService.record_detection(
            db, ThreatLogCreate(filename="a.exe", prediction="Trojan", confidence=90.0)
        )
        ThreatMonitoringService.record_detection(
            db, ThreatLogCreate(filename="b.exe", prediction="Benign", confidence=95.0)
        )
        ThreatMonitoringService.record_detection(
            db, ThreatLogCreate(filename="c.exe", prediction="Ransomware", confidence=85.0)
        )

        summary = ThreatMonitoringService.get_dashboard_summary(db)
        assert summary.total_files == 3
        assert summary.malware_files == 2
        assert summary.benign_files == 1
        assert summary.malware_percentage == pytest.approx(66.67, abs=0.1)

    def test_detection_trends(self, db):
        """Detection trends return data for each day."""
        ThreatMonitoringService.record_detection(
            db, ThreatLogCreate(filename="a.exe", prediction="Trojan", confidence=80.0)
        )

        trends = ThreatMonitoringService.get_detection_trends(db, days=7)
        assert trends.days == 7
        assert len(trends.data) == 7
        # At least the last day should have a detection
        assert any(d.total > 0 for d in trends.data)

    def test_malware_family_breakdown(self, db):
        """Family breakdown groups by prediction."""
        for _ in range(3):
            ThreatMonitoringService.record_detection(
                db, ThreatLogCreate(filename="a.exe", prediction="Trojan", confidence=80.0)
            )
        for _ in range(2):
            ThreatMonitoringService.record_detection(
                db, ThreatLogCreate(filename="b.exe", prediction="Worm", confidence=70.0)
            )

        breakdown = ThreatMonitoringService.get_malware_family_breakdown(db)
        assert breakdown.total_malware == 5
        assert len(breakdown.families) == 2
        assert breakdown.families[0].family == "Trojan"
        assert breakdown.families[0].count == 3

    def test_generate_report(self, db):
        """Report generation returns all sections."""
        ThreatMonitoringService.record_detection(
            db, ThreatLogCreate(filename="a.exe", prediction="Trojan", confidence=90.0)
        )

        report = ThreatMonitoringService.generate_threat_report(db, days=30)
        assert report.generated_at is not None
        assert report.summary.total_files == 1
        assert report.trends.days == 30
        assert len(report.trends.data) == 30
        assert isinstance(report.status_distribution, dict)

    def test_delete_threat(self, db):
        """Can delete a threat."""
        result = ThreatMonitoringService.record_detection(
            db, ThreatLogCreate(filename="a.exe", prediction="Trojan", confidence=80.0)
        )
        assert ThreatMonitoringService.delete_threat(db, result["threat_id"]) is True
        assert ThreatMonitoringService.get_threat_detail(db, result["threat_id"]) is None
