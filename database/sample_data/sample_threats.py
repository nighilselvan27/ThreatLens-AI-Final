"""
Seed script for populating the ThreatLens AI database with realistic sample
threat data for development and demonstration purposes.

Usage:
    cd backend
    python -m database.sample_data.sample_threats

Or import and call seed_threats(db_session) programmatically.
"""

import os
import sys
import uuid
import random
from datetime import datetime, timedelta, timezone

# Ensure imports work from any working directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


from sqlalchemy.orm import Session

from app.modules.threat_monitoring.models import (
    ThreatLog,
    ThreatTimelineEvent,
    ThreatStatus,
    RiskLevel,
    TimelineEventType,
)
from app.modules.threat_monitoring.risk_score import calculate_risk_score
from app.modules.threat_monitoring.repository import ThreatRepository


# ---------------------------------------------------------------------------
# Sample data pools
# ---------------------------------------------------------------------------

MALWARE_FAMILIES = [
    "Trojan",
    "Ransomware",
    "Worm",
    "Spyware",
    "Rootkit",
    "Backdoor",
    "Keylogger",
    "Adware",
    "Botnet",
    "Dropper",
    "RAT",
    "Exploit",
]

BENIGN_PREDICTIONS = ["Benign", "Clean", "Safe"]

SAMPLE_FILENAMES = [
    "invoice_2024_Q3.exe",
    "quarterly_report.pdf",
    "employee_database.xlsx",
    "system_update.dll",
    "project_proposal.docx",
    "financial_summary.zip",
    "hr_payroll_tool.exe",
    "marketing_deck.pptx",
    "config_backup.zip",
    "network_scanner.exe",
    "vpn_client_setup.exe",
    "database_migration.py",
    "admin_panel.dll",
    "security_patch.msi",
    "browser_extension.crx",
    "cloud_sync_agent.exe",
    "email_attachment.doc",
    "firmware_update.bin",
    "password_manager.exe",
    "remote_desktop.exe",
    "backup_restore.zip",
    "antivirus_crack.exe",
    "license_keygen.exe",
    "free_game_installer.exe",
    "crypto_miner.exe",
]

FILE_TYPES = ["exe", "dll", "pdf", "doc", "docx", "zip", "xlsx", "pptx", "msi", "py"]

DETECTION_ENGINES = [
    "ThreatLens AI",
    "ThreatLens Static Analyzer",
    "YARA Scanner",
    "Behavioral Analyzer",
    "Signature Engine",
]

YARA_RULE_POOL = [
    "MALWARE_Trojan_Generic",
    "MALWARE_Ransomware_CryptoLocker",
    "SUSPICIOUS_PowerShell_Invoke",
    "SUSPICIOUS_Encoded_Commands",
    "MALWARE_Backdoor_Meterpreter",
    "SUSPICIOUS_PE_Imports",
    "MALWARE_Keylogger_HookAPI",
    "SUSPICIOUS_Network_Callback",
    "MALWARE_Rootkit_Driver",
    "SUSPICIOUS_String_Obfuscation",
]

INDICATOR_KEYS = [
    "malicious_urls",
    "suspicious_ips",
    "encoded_powershell",
    "registry_modifications",
    "process_injection",
    "network_callbacks",
    "file_encryption_activity",
    "privilege_escalation",
]


def _random_hash(length: int = 64) -> str:
    """Generate a random hex hash of the given length."""
    return uuid.uuid4().hex[:length].ljust(length, "0")


def _random_datetime(days_back: int = 60) -> datetime:
    """Generate a random datetime within the last N days."""
    offset = random.randint(0, days_back * 24 * 3600)
    return datetime.now(timezone.utc) - timedelta(seconds=offset)


def _generate_sample_threat(index: int) -> dict:
    """Generate a single sample threat detection."""
    is_malware = random.random() < 0.7  # 70% malware, 30% benign

    if is_malware:
        prediction = random.choice(MALWARE_FAMILIES)
        confidence = round(random.uniform(55.0, 99.0), 1)
    else:
        prediction = random.choice(BENIGN_PREDICTIONS)
        confidence = round(random.uniform(70.0, 99.0), 1)

    filename = random.choice(SAMPLE_FILENAMES)
    file_type = filename.rsplit(".", 1)[-1] if "." in filename else "exe"

    yara_matches = None
    suspicious_indicators = None

    if is_malware:
        # Add YARA matches for ~60% of malware
        if random.random() < 0.6:
            yara_matches = random.sample(YARA_RULE_POOL, random.randint(1, 4))

        # Add suspicious indicators for ~50% of malware
        if random.random() < 0.5:
            indicator_count = random.randint(1, 4)
            chosen_keys = random.sample(INDICATOR_KEYS, indicator_count)
            suspicious_indicators = {
                key: [f"sample_{key}_value_{i}" for i in range(random.randint(1, 3))]
                for key in chosen_keys
            }

    risk_score, risk_level = calculate_risk_score(
        confidence=confidence,
        prediction=prediction,
        yara_matches=yara_matches,
        suspicious_indicators=suspicious_indicators,
    )

    detected_at = _random_datetime(days_back=60)

    # Determine status based on age
    if not is_malware:
        status = ThreatStatus.RESOLVED
    elif (datetime.now(timezone.utc) - detected_at).days > 14:
        status = random.choice([
            ThreatStatus.RESOLVED,
            ThreatStatus.CONFIRMED,
            ThreatStatus.FALSE_POSITIVE,
        ])
    elif (datetime.now(timezone.utc) - detected_at).days > 3:
        status = random.choice([
            ThreatStatus.UNDER_INVESTIGATION,
            ThreatStatus.CONFIRMED,
            ThreatStatus.QUARANTINED,
        ])
    else:
        status = random.choice([
            ThreatStatus.DETECTED,
            ThreatStatus.QUARANTINED,
            ThreatStatus.MONITORING,
        ])

    return {
        "filename": filename,
        "file_hash_md5": _random_hash(32),
        "file_hash_sha256": _random_hash(64),
        "file_size": random.randint(1024, 50 * 1024 * 1024),
        "file_type": file_type,
        "prediction": prediction,
        "confidence": confidence,
        "detection_engine": random.choice(DETECTION_ENGINES),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "status": status,
        "yara_matches": yara_matches,
        "static_analysis_results": {
            "pe_header": is_malware and random.random() < 0.5,
            "suspicious_imports": random.randint(0, 15) if is_malware else 0,
            "entropy_score": round(random.uniform(3.0, 8.0), 2),
        },
        "suspicious_indicators": suspicious_indicators,
        "description": (
            f"File '{filename}' classified as {prediction} with {confidence}% confidence. "
            f"Risk level: {risk_level}."
        ),
        "recommended_action": (
            f"{'Escalate to SOC team' if risk_level in ('critical', 'high') else 'Monitor and review'}."
        ),
        "detected_at": detected_at,
    }


def seed_threats(db: Session, count: int = 50) -> list:
    """
    Seed the database with sample threat detections.

    Args:
        db: SQLAlchemy database session.
        count: Number of sample threats to create.

    Returns:
        List of created ThreatLog IDs.
    """
    created_ids = []

    for i in range(count):
        data = _generate_sample_threat(i)

        threat = ThreatLog(
            id=str(uuid.uuid4()),
            filename=data["filename"],
            file_hash_md5=data["file_hash_md5"],
            file_hash_sha256=data["file_hash_sha256"],
            file_size=data["file_size"],
            file_type=data["file_type"],
            prediction=data["prediction"],
            confidence=data["confidence"],
            detection_engine=data["detection_engine"],
            risk_score=data["risk_score"],
            risk_level=data["risk_level"],
            status=data["status"],
            yara_matches=data["yara_matches"],
            static_analysis_results=data["static_analysis_results"],
            suspicious_indicators=data["suspicious_indicators"],
            description=data["description"],
            recommended_action=data["recommended_action"],
            detected_at=data["detected_at"],
        )

        saved = ThreatRepository.save_threat(db, threat)
        created_ids.append(saved.id)

        # Add timeline events
        ThreatRepository.add_timeline_event(
            db,
            threat_id=saved.id,
            event_type=TimelineEventType.DETECTED,
            description=f"{'Malware' if data['prediction'] not in ('Benign', 'Clean', 'Safe') else 'File'} detected: {data['prediction']}",
            created_by="system",
        )

        # Add more timeline events for older threats
        if data["status"] != ThreatStatus.DETECTED:
            ThreatRepository.add_timeline_event(
                db,
                threat_id=saved.id,
                event_type=TimelineEventType.ANALYZED,
                description=f"Static analysis completed. Risk score: {data['risk_score']}",
                created_by="system",
            )

        if data["status"] in (ThreatStatus.RESOLVED, ThreatStatus.FALSE_POSITIVE):
            ThreatRepository.add_timeline_event(
                db,
                threat_id=saved.id,
                event_type=TimelineEventType.RESOLVED,
                description=f"Threat {data['status'].value}",
                created_by="analyst",
            )

    print(f"✅ Seeded {count} sample threats ({len(created_ids)} created)")
    return created_ids


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from app.database.database import engine, Base, SessionLocal

    # Import models to register tables
    import app.models.user  # noqa
    import app.modules.threat_monitoring.models  # noqa

    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_threats(db, count=50)
    finally:
        db.close()

    print("🎉 Seeding complete!")
