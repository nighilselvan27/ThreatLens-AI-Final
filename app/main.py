"""
Standalone entrypoint for the Alert & Notification module.

This lets Member 6's module run and be tested independently ("python -m
uvicorn app.main:app --reload"). Once the team's main FastAPI app exists,
DO NOT run this file in production — instead mount `alerts_router` from
`app.routes.alerts` onto the shared app, e.g.:

    from member6_alert_notification.app.routes.alerts import router as alerts_router
    main_app.include_router(alerts_router)

and call `init_db()` (or run an Alembic migration) as part of the shared
app's startup instead of the standalone startup event below.
"""
from fastapi import FastAPI

from app.database import init_db
from app.routes.alerts import router as alerts_router

app = FastAPI(title="ThreatLens AI — Alert & Notification Module (Member 6)")

app.include_router(alerts_router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "module": "alert-notification"}
