from fastapi import FastAPI
from app.api.upload import router as upload_router

app = FastAPI(
    title="ThreatLens Malware Detection API",
    version="1.0.0"
)

app.include_router(upload_router)

@app.get("/")
def home():
    return {
        "message": "ThreatLens Backend Running"
    }