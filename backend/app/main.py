from fastapi import FastAPI
from app.database.database import engine, Base
import app.models.user  # Ensure User model is loaded into Base.metadata

# Create database tables automatically
Base.metadata.create_all(bind=engine)



# Existing Upload Router
from app.api.upload import router as upload_router

# Authentication Router
from app.controllers.auth_controller import router as auth_router

app = FastAPI(
    title="ThreatLens Malware Detection API",
    version="1.0.0"
)

# Existing Routes
app.include_router(upload_router)

# Authentication Routes
app.include_router(auth_router)


@app.get("/")
def home():
    return {
        "message": "ThreatLens Backend Running"
    }