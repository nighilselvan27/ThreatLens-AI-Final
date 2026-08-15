from fastapi import FastAPI
from app.api.upload import router as upload_router
from app.alerts.router import router as alerts_router
from app.alerts.database import Base as alerts_base, engine as alerts_engine

app = FastAPI(
    title="ThreatLens Malware Detection API",
    version="1.0.0"
)

# TEMPORARY: creates the `alerts` table if it doesn't exist yet. Member 1
# hasn't published Alembic migrations for the project, so this mirrors the
# same create_all()-on-startup approach used elsewhere until real
# migrations exist. Once they do, remove this and add an alerts migration
# instead (see backend/app/alerts/README.md).
alerts_base.metadata.create_all(bind=alerts_engine)

app.include_router(upload_router)
app.include_router(alerts_router)

@app.get("/")
def home():
    return {
        "message": "ThreatLens Backend Running"
    }