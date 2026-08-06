# Alert & Notification Module

Member 6's module for the **Malware Detection & Threat Intelligence Platform**.

Turns confirmed malware detections (from the Threat Monitoring module) into
persisted alert records and email notifications, and exposes REST APIs for
the frontend to read alert history.

## Responsibilities

- Malware alerts — structured alert records created from detections
- Email notifications — SMTP-based alerts to users/admins
- Security warnings — severity classification (low/medium/high/critical)
- Detection status tracking — new / acknowledged / resolved
- Alert history — persisted, queryable log
- Notification APIs — REST endpoints for other modules and the frontend
- *(Optional, later)* VirusTotal integration for reputation enrichment

## Project Structure

```
alert-notification-module/
  app/
    main.py                 FastAPI app entrypoint
    config.py                Settings loaded from environment variables
    database.py               SQLAlchemy engine & session
    models.py                  Alert SQLAlchemy model
    schemas.py                  Pydantic request/response schemas
    routers/
      alerts.py                Notification API endpoints
    services/
      alert_service.py         Core alert creation/lookup logic
      email_service.py         SMTP email sending
    templates/
      alert_email.html         HTML email template
  requirements.txt
  .env.example
  README.md
```

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in DB + SMTP credentials
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs` once running.

## API Endpoints

| Method | Path                        | Description                              |
|--------|-----------------------------|-------------------------------------------|
| POST   | `/api/alerts`                | Create a new alert + send email          |
| GET    | `/api/alerts`                 | List alerts (filter by status/severity)  |
| GET    | `/api/alerts/{alert_id}`       | Get a single alert                       |
| PATCH  | `/api/alerts/{alert_id}/status` | Update alert status                    |
| GET    | `/health`                       | Health check                           |

## Integration Points

- **Member 5 (Threat Monitoring):** calls `POST /api/alerts` when the AI model
  confirms a malware detection.
- **Member 7 (Frontend):** calls `GET /api/alerts` to populate the Alerts and
  Threat Details pages.
- **Member 1 (User Management):** supplies `recipient_user_id` / JWT auth;
  this module reuses the same PostgreSQL instance.

## Status

- [x] Alert model + database setup
- [x] Alert creation service
- [x] SMTP email notifications
- [x] REST APIs (create / list / get / update status)
- [ ] Wire up to real Threat Monitoring output
- [ ] Optional: VirusTotal enrichment
