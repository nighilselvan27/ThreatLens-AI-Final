"""
ThreatLens AI — Main FastAPI Application

Registers all routers and initialises the database tables on startup.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.database import engine, Base
from app.models import user as _user_model  # Ensure User model is loaded into Base.metadata

# Import Threat Monitoring models so they register with Base.metadata
from app.modules.threat_monitoring import models as _threat_models  # noqa: F401


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-35s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("threatlens")


# ---------------------------------------------------------------------------
# Application lifespan — startup / shutdown hooks
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup:
        1. Create all database tables (PostgreSQL / SQLite)
        2. Initialise MongoDB connection for detection audit logging
    Shutdown:
        1. Close MongoDB connection
    """
    # --- Startup ---
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created.")

    # Initialise MongoDB (graceful fallback if unavailable)
    try:
        from app.modules.threat_monitoring.mongo_connection import init_mongo_connection
        mongo_ok = init_mongo_connection()
        if mongo_ok:
            logger.info("MongoDB connection established for detection logging.")
        else:
            logger.warning(
                "MongoDB unavailable — detection audit logging will be skipped. "
                "PostgreSQL logging is unaffected."
            )
    except Exception as e:
        logger.warning("MongoDB initialisation error: %s", str(e))

    yield

    # --- Shutdown ---
    try:
        from app.modules.threat_monitoring.mongo_connection import close_mongo_connection
        close_mongo_connection()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="ThreatLens Malware Detection API",
    description=(
        "AI-powered malware classification and threat detection platform. "
        "Provides file upload, static analysis, malware classification, "
        "threat monitoring, alert notifications, and analytics dashboards."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS Middleware — allow frontend to communicate with backend
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",       # Vite dev server
        "http://localhost:3000",       # Alternative dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register Routers
# ---------------------------------------------------------------------------

# Existing Upload Router
from app.api.upload import router as upload_router
app.include_router(upload_router)

# Authentication Router
from app.controllers.auth_controller import router as auth_router
app.include_router(auth_router)

# Threat Monitoring Router
from app.api.threat_monitoring import router as threat_monitoring_router
app.include_router(threat_monitoring_router)

# Alert & Notification Router
try:
    from app.alerts.router import router as alerts_router
    from app.alerts import models as _alert_models  # noqa: F401
    app.include_router(alerts_router)
except Exception as e:

    logger.warning("Could not register alerts_router: %s", str(e))


# ---------------------------------------------------------------------------
# Root Health Check
# ---------------------------------------------------------------------------

@app.get("/", tags=["Health"])
def home():
    """Health check endpoint."""
    return {
        "message": "ThreatLens Backend Running",
        "version": "1.0.0",
        "modules": {
            "auth": "active",
            "upload": "active",
            "threat_monitoring": "active",
            "alerts": "active",
        },
    }



@app.get("/health", tags=["Health"])
def health_check():
    """Detailed health check with MongoDB status."""
    mongo_status = "unavailable"
    try:
        from app.modules.threat_monitoring.mongo_connection import mongo_available
        if mongo_available():
            mongo_status = "connected"
    except Exception:
        pass

    return {
        "status": "healthy",
        "database": "connected",
        "mongodb": mongo_status,
    }