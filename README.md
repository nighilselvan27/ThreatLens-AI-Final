# Member 6 — Alert & Notification Module

Implements the PDF's **"6. Alert & Notification Module"**: malware alerts,
threat notifications, detection status updates, and security warnings,
matching the Alert Service block in the architecture diagram (Threat
Alerts / Email Notifications / Dashboard Alerts / Incident Creation).

This is a self-contained package. The main repo currently has no other
code (just `README.md`/`LICENSE`), so no existing conventions were
available to follow — see "Integration notes" below for what will need to
change once other members' code lands.

## Stack (matches the PDF)
Python, FastAPI, SQLAlchemy (PostgreSQL-ready, SQLite fallback for local
dev), Pydantic, JWT-based auth hook, SMTP email notifications, pytest.

## Running standalone
```bash
cd member6_alert_notification
pip install -r requirements.txt
cp .env.example .env   # edit as needed; defaults to SQLite + auth off
uvicorn app.main:app --reload
```

## Running tests
```bash
cd member6_alert_notification
PYTHONPATH=. pytest tests/ -v
```

## Integration Contract

```
Input (from Member 3 - Classification, or Member 5 - Monitoring):
  ThreatDetectionResult {
    detection_id: str        (required, unique)
    file_id: str | null
    malware_family: str | null
    risk_score: float        (required, 0-100)
    confidence_score: float | null (0-1)
    source_module: str       ("classification" | "monitoring")
  }

Processing:
  - Deduplicate by detection_id (idempotent)
  - Map risk_score -> severity (low/medium/high/critical)
  - Route high/critical -> security_analyst role, else -> soc_team role
  - Persist Alert record
  - Dispatch notification (email if SMTP configured, else console/log)

Output:
  Alert {
    id, detection_id, file_id, malware_family, risk_score, confidence_score,
    severity, status, title, message, recipient_role,
    notified, notification_channel, created_at, updated_at, resolved_at
  }

API:
  POST   /alerts/ingest            - submit a ThreatDetectionResult -> Alert
  GET    /alerts/                  - list alerts (filter by status/severity/role)
  GET    /alerts/{alert_id}        - get one alert
  PATCH  /alerts/{alert_id}/status - transition status

Database:
  New table only: `alerts` (owned by Member 6). No existing tables
  modified — there were none.
```

## Integration notes (read before merging)

1. **Auth (`app/auth/dependencies.py`)** is a placeholder JWT decoder.
   Replace it with Member 1's real `get_current_user` once the User
   Management module exists; delete this file rather than keeping two
   auth implementations.
2. **Database (`app/database.py`)** creates its own SQLAlchemy `engine`/
   `Base`. If/when a shared `Base`/session factory exists, point
   `app/models/alert.py` at that instead and delete this file.
3. **`detection_id` / `file_id` / `recipient_role`** in the `Alert` model
   are plain string columns, not real foreign keys, because the tables
   they'd reference (detections, files, users) don't exist yet. Convert
   to `ForeignKey` once those tables land (marked with `TODO(integration)`
   comments in `app/models/alert.py`).
4. **Mounting into the main app**, once one exists:
   ```python
   from member6_alert_notification.app.routes.alerts import router as alerts_router
   main_app.include_router(alerts_router)
   ```
5. **Config (`app/config.py`)** reads everything from environment
   variables (see `.env.example`). If the team adopts a shared settings
   module, migrate these values there.

## Testing summary
16 tests, all passing (`pytest tests/ -v`):
- **Normal:** alert creation from high/low risk detections, severity→role
  routing, listing with filters, status updates.
- **Edge:** duplicate detection_id (idempotency), missing optional
  fields, out-of-range risk_score validation, updating a nonexistent
  alert.
- **Failure:** fetching a nonexistent alert, malformed ingest payload
  (422), SMTP unavailable (verified separately — falls back to console
  logging rather than raising, see `app/services/notifier.py`).

Also manually verified end-to-end against a live `uvicorn` process
(`POST /alerts/ingest` → `GET /alerts/`), not just the test client.
