"""
FastAPI application entrypoint for the Alert & Notification Module.

Run locally:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import alerts

# Creates the `alerts` table if it doesn't already exist.
# In production, use Alembic migrations instead of create_all().
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Alert & Notification Module",
    description="Generates and delivers malware detection alerts for the platform.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to the frontend's origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alerts.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "module": "alert-notification"}
