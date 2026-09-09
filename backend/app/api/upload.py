import os
import uuid
import shutil

from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

UPLOAD_FOLDER = "storage/uploaded_files"

# Create folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {
    ".exe",
    ".dll",
    ".pdf",
    ".doc",
    ".docx",
    ".zip"
}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Get file extension
    extension = os.path.splitext(file.filename)[1].lower()

    # Validate extension
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type"
        )

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{extension}"

    # Full path
    file_path = os.path.join(
        UPLOAD_FOLDER,
        unique_filename
    )

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "message": "File uploaded successfully",
        "original_filename": file.filename,
        "stored_filename": unique_filename
    }