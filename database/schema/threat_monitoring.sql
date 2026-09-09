-- =====================================================================
-- ThreatLens AI — Threat Monitoring Module
-- PostgreSQL DDL Script
-- Target Tables: threat_logs, threat_timeline_events
-- =====================================================================

-- =====================================================================
-- Table: threat_logs
-- Stores every file scan / AI prediction result
-- =====================================================================

CREATE TABLE IF NOT EXISTS threat_logs (
    id              VARCHAR(36) PRIMARY KEY,

    -- File metadata
    filename        VARCHAR(500) NOT NULL,
    file_hash_md5   VARCHAR(32),
    file_hash_sha256 VARCHAR(64),
    file_size       INTEGER,
    file_type       VARCHAR(50),

    -- AI prediction results
    prediction      VARCHAR(100) NOT NULL,
    confidence      FLOAT NOT NULL DEFAULT 0.0,
    detection_engine VARCHAR(100) DEFAULT 'ThreatLens AI',

    -- Risk assessment
    risk_score      INTEGER NOT NULL DEFAULT 0,
    risk_level      VARCHAR(20) NOT NULL DEFAULT 'minimal'
                    CHECK (risk_level IN ('critical', 'high', 'medium', 'low', 'minimal')),

    -- Status tracking
    status          VARCHAR(30) NOT NULL DEFAULT 'detected'
                    CHECK (status IN (
                        'detected', 'quarantined', 'under_investigation',
                        'confirmed', 'resolved', 'false_positive', 'monitoring'
                    )),

    -- Static analysis artifacts (stored as JSON)
    yara_matches            JSON,
    static_analysis_results JSON,
    suspicious_indicators   JSON,

    -- Description & notes
    description         TEXT,
    recommended_action  TEXT,
    notes               TEXT,

    -- Ownership
    detected_by_user_id INTEGER,

    -- Timestamps
    detected_at     TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    resolved_at     TIMESTAMP WITH TIME ZONE
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_threat_logs_filename        ON threat_logs (filename);
CREATE INDEX IF NOT EXISTS idx_threat_logs_hash_md5        ON threat_logs (file_hash_md5);
CREATE INDEX IF NOT EXISTS idx_threat_logs_hash_sha256     ON threat_logs (file_hash_sha256);
CREATE INDEX IF NOT EXISTS idx_threat_logs_prediction      ON threat_logs (prediction);
CREATE INDEX IF NOT EXISTS idx_threat_logs_risk_level      ON threat_logs (risk_level);
CREATE INDEX IF NOT EXISTS idx_threat_logs_status          ON threat_logs (status);
CREATE INDEX IF NOT EXISTS idx_threat_logs_detected_at     ON threat_logs (detected_at);
CREATE INDEX IF NOT EXISTS idx_threat_logs_hash_prediction ON threat_logs (file_hash_sha256, prediction);
CREATE INDEX IF NOT EXISTS idx_threat_logs_detected_risk   ON threat_logs (detected_at, risk_level);


-- =====================================================================
-- Table: threat_timeline_events
-- Chronological event log per threat
-- =====================================================================

CREATE TABLE IF NOT EXISTS threat_timeline_events (
    id          VARCHAR(36) PRIMARY KEY,

    threat_id   VARCHAR(36) NOT NULL
                REFERENCES threat_logs (id) ON DELETE CASCADE,

    event_type  VARCHAR(30) NOT NULL
                CHECK (event_type IN (
                    'detected', 'analyzed', 'escalated', 'status_changed',
                    'note_added', 'resolved', 'reopened', 'alert_created'
                )),

    description TEXT NOT NULL,

    -- Who triggered this event (nullable for system events)
    created_by  VARCHAR(255),

    created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_timeline_threat_id   ON threat_timeline_events (threat_id);
CREATE INDEX IF NOT EXISTS idx_timeline_created_at  ON threat_timeline_events (created_at);


-- =====================================================================
-- Auto-update trigger for threat_logs.updated_at
-- =====================================================================

CREATE OR REPLACE FUNCTION update_threat_logs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

DROP TRIGGER IF EXISTS trg_update_threat_logs_updated_at ON threat_logs;
CREATE TRIGGER trg_update_threat_logs_updated_at
BEFORE UPDATE ON threat_logs
FOR EACH ROW
EXECUTE FUNCTION update_threat_logs_updated_at();
