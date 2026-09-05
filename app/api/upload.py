import os
import uuid
import shutil
import hashlib
import magic
import mimetypes
import pefile
import re
import yara
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

UPLOAD_FOLDER = "storage/uploaded_files"
YARA_RULES = "yara_rules/malware_rules.yar"
REPORTS = {}
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
def calculate_hashes(file_path):
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(4096):
            md5.update(chunk)
            sha256.update(chunk)

    return {
        "md5": md5.hexdigest(),
        "sha256": sha256.hexdigest()
    }
def extract_metadata(file_path, original_filename):
    file_stats = os.stat(file_path)

    return {
        "filename": original_filename,
        "extension": os.path.splitext(original_filename)[1].lower(),
        "size_bytes": file_stats.st_size,
        "mime_type": mimetypes.guess_type(original_filename)[0],
        "created_at": datetime.fromtimestamp(
            file_stats.st_ctime
        ).isoformat(),
        "modified_at": datetime.fromtimestamp(
            file_stats.st_mtime
        ).isoformat()
    }
def detect_file_type(file_path):
    mime_type = magic.from_file(file_path, mime=True)
    description = magic.from_file(file_path)

    return {
        "mime_type": mime_type,
        "description": description
    }
def analyze_pe_header(file_path):
    try:
        pe = pefile.PE(file_path)

        return {
            "machine": hex(pe.FILE_HEADER.Machine),
            "number_of_sections": pe.FILE_HEADER.NumberOfSections,
            "timestamp": pe.FILE_HEADER.TimeDateStamp,
            "entry_point": hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint),
            "image_base": hex(pe.OPTIONAL_HEADER.ImageBase),
            "subsystem": pe.OPTIONAL_HEADER.Subsystem,
            "characteristics": hex(pe.FILE_HEADER.Characteristics)
        }

    except pefile.PEFormatError:
        return {
            "error": "Not a valid PE file"
        }
def analyze_imports(file_path):
    try:
        pe = pefile.PE(file_path)

        imports = {}

        if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
            for entry in pe.DIRECTORY_ENTRY_IMPORT:
                dll_name = entry.dll.decode(
                    "utf-8", errors="ignore"
                )

                api_names = []

                for imp in entry.imports:
                    if imp.name:
                        api_names.append(
                            imp.name.decode(
                                "utf-8", errors="ignore"
                            )
                        )
                    else:
                        api_names.append(
                            f"Ordinal_{imp.ordinal}"
                        )

                imports[dll_name] = api_names

        return imports

    except pefile.PEFormatError:
        return {
            "error": "Not a valid PE file"
        }
def detect_urls_ips(file_path):
    with open(file_path, "rb") as file:
        data = file.read()

    text = data.decode("latin-1", errors="ignore")

    url_pattern = r"https?://[^\s\"'<>]+"
    ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"

    urls = sorted(set(re.findall(url_pattern, text)))
    ips = sorted(set(re.findall(ip_pattern, text)))

    return {
        "urls": urls,
        "ip_addresses": ips
    }
def run_yara(file_path):
    try:
        rules = yara.compile(filepath=YARA_RULES)
        matches = rules.match(file_path)

        return {
            "matched_rules": [match.rule for match in matches]
        }

    except Exception as e:
        return {
            "error": str(e)
        }
def generate_analysis_report(
    metadata,
    file_type,
    pe_header,
    imports,
    urls_ips,
    yara_results,
    hashes
):
    report = {
        "summary": {
            "filename": metadata["filename"],
            "file_type": file_type["description"],
            "file_size": metadata["size_bytes"],
            "md5": hashes["md5"],
            "sha256": hashes["sha256"]
        },

        "analysis": {
            "pe_file":
                "Yes" if "error" not in pe_header else "No",

            "imports_found":
                len(imports) if isinstance(imports, dict) else 0,

            "urls_found":
                len(urls_ips["urls"]),

            "ip_addresses_found":
                len(urls_ips["ip_addresses"]),

            "yara_matches":
                yara_results.get("matched_rules", [])
        }
    }

    return report
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

    hashes = calculate_hashes(file_path)
    metadata = extract_metadata(file_path, file.filename)
    file_type = detect_file_type(file_path)
    pe_header = analyze_pe_header(file_path)
    imports = analyze_imports(file_path)
    urls_ips = detect_urls_ips(file_path)
    yara_results = run_yara(file_path)

    analysis_report = generate_analysis_report(
        metadata,
        file_type,
        pe_header,
        imports,
        urls_ips,
        yara_results,
        hashes
    )

    REPORTS[unique_filename] = analysis_report

    return {
        "message": "File uploaded successfully",
        "original_filename": file.filename,
        "stored_filename": unique_filename,
        "report_url": f"/report/{unique_filename}",
        "hashes": hashes,
        "metadata": metadata,
        "file_type": file_type,
        "pe_header": pe_header,
        "imports": imports,
        "urls_ips": urls_ips,
        "yara_results": yara_results
    }

@router.get("/report/{stored_filename}")
def get_analysis_report(stored_filename: str):

    report = REPORTS.get(stored_filename)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found"
        )

    return report