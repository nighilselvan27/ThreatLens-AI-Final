# Alert & Notification Module (Member 6)

Turns confirmed threat detections from the Threat Monitoring module (Member 5)
into persisted, queryable `Alert` records, notifies recipients by email, and
exposes REST APIs consumed by the frontend (Member 7).

## Location & why it moved

An earlier, standalone version of this module lived at the repo root
(`main.py`, `alert_service.py`, etc.) but its imports assumed an `app/`
package that didn't exist there, so it never actually ran. It has been
rebuilt here, inside the team's real backend (`backend/app/alerts/`),
matching the folder every other module lives in.

## Files

```
backend/app/alerts/
  __init__.py
  config.py           Settings (env vars) — see docstring for what's temporary
  database.py         SQLAlchemy engine/session — see docstring for what's temporary
  models.py           Alert ORM model + Severity / AlertStatus / AlertType enums
  schemas.py          Pydantic request/response schemas (AlertOut is camelCase
                       to match the frontend's Alert interface exactly)
  auth_stub.py         TEMPORARY JWT/RBAC dependency — replace once Member 1
                       ships backend/app/auth/
  service.py           Core logic: create (with dedup), list (RBAC-scoped),
                       get, mark-read, status update, resolve, delete, stats
  adapters.py           Translates Member 5's detection payload into an
                       AlertCreate — READ THIS to wire up Member 5's module
  notifier.py           Extensible notification dispatch (email today;
                       add channels here without touching service.py)
  email_service.py     SMTP sending + Jinja2 rendering
  templates/alert_email.html
```

## Setup

From the repo root:
```
pip install -r requirements.txt
cp .env.example .env   # fill in DATABASE_URL, SMTP_*, JWT_SECRET_KEY, ALERT_INGEST_API_KEY
cd backend
uvicorn app.main:app --reload
```
API docs at `http://localhost:8000/docs`.

## API Endpoints

All under `/api/v1/alerts` (matches the frontend's `VITE_API_BASE_URL` default).

| Method | Path                        | Auth                          | Description |
|--------|-----------------------------|--------------------------------|-------------|
| POST   | `/api/v1/alerts/ingest`     | `X-Internal-Api-Key` header    | Service-to-service alert creation (Member 5 → Member 6) |
| POST   | `/api/v1/alerts`            | JWT — analyst/admin            | Manual alert creation |
| GET    | `/api/v1/alerts`            | JWT — any role                 | List alerts (filters: `status`, `severity`, `unread_only`, `limit`, `offset`) |
| GET    | `/api/v1/alerts/stats/summary` | JWT — any role              | Counts: total/unread/critical/active/resolved + breakdowns |
| GET    | `/api/v1/alerts/{id}`       | JWT — any role                 | Single alert |
| PATCH  | `/api/v1/alerts/{id}/read`  | JWT — any role                 | Mark as read |
| PATCH  | `/api/v1/alerts/{id}/status`| JWT — analyst/admin            | Body: `{"status": "..."}` |
| PATCH  | `/api/v1/alerts/{id}/resolve`| JWT — analyst/admin           | Shortcut to status=resolved |
| DELETE | `/api/v1/alerts/{id}`       | JWT — admin only               | Hard delete |

See the router docstring for the full RBAC table and the assumptions behind it.

## Member 5 integration (Threat Monitoring → Alerts)

Member 5's module isn't runnable yet (`backend/app/modules/threat_monitoring`
is an empty file, not the package `Service.py` tries to import from). Until
it's fixed, `adapters.py` documents and implements the exact translation from
their `ThreatMonitoringService.save_detection()` return shape into an
`AlertCreate`, plus the severity mapping used. Read the module docstring in
`adapters.py` — it has copy-pasteable "Option A / Option B" wiring code for
whoever finishes Member 5's module.

## Member 7 integration (Alerts → Frontend)

`GET /api/v1/alerts` returns exactly the shape `frontend/src/types/alert.types.ts`
expects (`id, title, message, severity, isRead, createdAt, source`), plus
extra fields the current frontend ignores. Severity values match
`frontend/src/types/threat.types.ts`'s `Severity` type exactly
(`critical | high | medium | low | info`). Swapping
`frontend/src/api/alertsApi.ts` from its current mock implementation to real
`axiosInstance` calls should require no other frontend changes; `markAsRead`
maps to `PATCH /{id}/read`, `deleteAlert` maps to `DELETE /{id}` (note: real
delete requires an administrator-role token — the frontend's mock had no such
restriction, so decide whether non-admins should call `/status` with
`false_positive` instead of a hard delete).

## Deduplication

See the docstring at the top of `service.py`. Summary: exact match on
`(source_reference_id, alert_type)` when available, else a 15-minute
fallback window on `(file_hash_sha256, alert_type)` — configurable via
`ALERT_DEDUP_WINDOW_MINUTES`.

## Known temporary pieces (for Member 8)

- `config.py` / `database.py`: self-contained until Member 1 publishes shared
  versions in `backend/app/config/` / `backend/app/database/` — see each
  file's docstring for the exact swap steps.
- `auth_stub.py`: decodes JWTs itself since `backend/app/auth/` is empty.
  Replace with Member 1's real dependency once available (same interface:
  needs `.user_id` and `.role`).
- `backend/app/main.py` creates the `alerts` table via `create_all()` on
  startup rather than an Alembic migration, since no migrations exist yet
  anywhere in the repo.
- Assumed JWT claims: `sub` (user id), `role` (one of `security_analyst`,
  `soc_team_member`, `administrator`, `researcher`). Confirm against
  Member 1's actual token shape once built.

## Testing

```
cd backend
pip install -r ../requirements.txt pytest httpx python-multipart
DATABASE_URL=sqlite:///./test_alerts.db ALERT_INGEST_API_KEY=test-key \
    pytest ../tests/backend_tests/test_alerts.py -v
```
23 tests covering creation, retrieval, read/status/resolve transitions,
auth/RBAC (401/403), invalid input (422), duplicate prevention, the
Member 5 adapter (including severity mapping and benign-skip), and stats.
