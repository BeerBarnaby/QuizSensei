"""
Pydantic schemas for document-related data.
Defines models for file uploads, health checks, and text extraction responses.
"""
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Returned after a successful file upload."""

    filename: str = Field(..., description="Original filename as uploaded by the client.")
    saved_as: str = Field(..., description="Filename stored on disk (may be sanitised/unique).")
    size_bytes: int = Field(..., description="Size of the uploaded file in bytes.")
    extension: str = Field(..., description="Lowercase file extension, e.g. '.pdf'.")
    upload_path: str = Field(..., description="Relative path where the file was saved.")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="UTC timestamp of the upload.")

    model_config = {"json_schema_extra": {
        "example": {
            "filename": "lecture_notes.pdf",
            "saved_as": "lecture_notes.pdf",
            "size_bytes": 204800,
            "extension": ".pdf",
            "upload_path": "uploads/lecture_notes.pdf",
            "uploaded_at": "2026-03-13T10:00:00Z",
        }
    }}


class HealthResponse(BaseModel):
    """Simple liveness-check response."""

    status: str = Field(default="ok")
    app: str
    version: str


# ---------------------------------------------------------------------------
# Extraction Phase 2 Schemas
# ---------------------------------------------------------------------------

class ExtractionMetadataResponse(BaseModel):
    """Metadata response when extraction succeeds or fails (no full text)."""
    document_id: str
    filename: str
    extension: str
    extraction_status: str = Field(..., description="'success' or 'failed'")
    char_count: int
    message: str | None = None

class ExtractionContentResponse(ExtractionMetadataResponse):
    """Full extraction response including the extracted text body."""
    extracted_text: str | None = None

class ExtractionPreviewResponse(ExtractionMetadataResponse):
    """Preview response including a short snippet of the text."""
    preview_text: str | None = None



