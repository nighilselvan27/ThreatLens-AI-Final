"""
INTEGRATION STUB — not Member 6's implementation.

This defines the `ThreatDetectionResult` shape Member 6's Alert module
expects to receive from:
  - Member 3 (Malware Classification / AI Prediction Module), and/or
  - Member 5 (Threat Monitoring Module)

This is a *contract*, not a real detection pipeline. Members 3/5 own the
actual implementation and should either:
  (a) call `create_alert_from_detection()` directly with an instance of
      this shape once their code produces one, or
  (b) POST this same JSON shape to `POST /alerts/ingest`.

Field names/types here are based on the PDF's stated outputs for those
modules (malware family, risk score, confidence/category mapping). If the
real implementation differs, update this schema — do not silently adapt
Member 6's internals around undocumented assumptions.
"""
from typing import Optional

from pydantic import BaseModel, Field


class ThreatDetectionResult(BaseModel):
    detection_id: str = Field(..., description="Unique ID of the detection/classification event")
    file_id: Optional[str] = Field(None, description="ID of the analyzed file, if applicable")
    malware_family: Optional[str] = Field(None, description="e.g. 'Trojan', 'Ransomware'")
    risk_score: float = Field(..., ge=0, le=100, description="0-100 risk score from classification")
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Model confidence, 0-1")
    source_module: str = Field(
        "unknown", description="Which module produced this: 'classification' or 'monitoring'"
    )
