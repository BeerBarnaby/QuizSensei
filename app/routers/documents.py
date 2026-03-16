
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.schemas.document import (
    DocumentUploadResponse,
    ExtractionMetadataResponse,
    ExtractionContentResponse,
    ExtractionPreviewResponse
)
from app.schemas.analysis import AnalysisResultResponse
from app.schemas.question import QuestionGenerationResponse, QuestionGenerationRequest, QuestionDraft
from app.services.document_service import DocumentService
from app.services.analysis_service import AnalysisService
from app.services.question_service import QuestionGenerationService

# FastAPI dependency to inject DocumentService
def get_document_service(settings: Settings = Depends(get_settings)) -> DocumentService:
    return DocumentService(settings)

# FastAPI dependency to inject AnalysisService
def get_analysis_service(settings: Settings = Depends(get_settings)) -> AnalysisService:
    return AnalysisService(settings)

# FastAPI dependency to inject QuestionGenerationService
def get_question_service(settings: Settings = Depends(get_settings)) -> QuestionGenerationService:
    return QuestionGenerationService(settings)

router = APIRouter(prefix="/documents", tags=["documents"])



def _validate_extension(filename: str, allowed: set[str]) -> str:
    ext = Path(filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"File type '{ext}' is not supported. "
                f"Allowed types: {sorted(allowed)}"
            ),
        )
    return ext


def _safe_filename(original: str) -> str:
    stem = Path(original).stem
    suffix = Path(original).suffix.lower()
    safe_stem = "".join(c if c.isalnum() or c in "-_." else "_" for c in stem)
    short_uid = uuid.uuid4().hex[:8]
    return f"{short_uid}_{safe_stem}{suffix}"


@router.get(
    "/",
    summary="List all uploaded documents",
    description="Returns metadata for all files currently present in the upload directory.",
)
async def list_documents(
    settings: Settings = Depends(get_settings),
) -> list:
    docs = []
    for f in settings.UPLOAD_DIR.iterdir():
        if f.is_file():
            docs.append({
                "document_id": f.name,
                "filename": f.name,
                "size_bytes": f.stat().st_size,
                "extension": f.suffix.lower(),
            })
    docs.sort(key=lambda x: x["document_id"])
    return docs


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    description=(
        "Upload a document (PDF, TXT, DOC, DOCX). "
        "The file is saved to the configured upload directory. "
        "Max file size is controlled by `MAX_FILE_SIZE_BYTES` in settings."
    ),
)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload."),
    settings: Settings = Depends(get_settings),
) -> DocumentUploadResponse:
    # ── 1. Extension validation ────────────────────────────────────────────
    ext = _validate_extension(file.filename or "", settings.ALLOWED_EXTENSIONS)

    # ── 2. Read file content (enforce size limit) ──────────────────────────
    content = await file.read()
    size_bytes = len(content)

    if size_bytes > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File size {size_bytes:,} bytes exceeds the maximum allowed "
                f"{settings.MAX_FILE_SIZE_BYTES:,} bytes."
            ),
        )

    if size_bytes == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    # ── 3. Persist to disk ─────────────────────────────────────────────────
    settings.ensure_upload_dir()
    saved_name = _safe_filename(file.filename or "document")
    dest_path: Path = settings.UPLOAD_DIR / saved_name

    async with aiofiles.open(dest_path, "wb") as out_file:
        await out_file.write(content)

    # ── 4. Return structured response ──────────────────────────────────────
    return DocumentUploadResponse(
        filename=file.filename or "unknown",
        saved_as=saved_name,
        size_bytes=size_bytes,
        extension=ext,
        upload_path=str(dest_path),
        uploaded_at=datetime.now(timezone.utc),
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a document",
    description="Deletes the specified document and its associated sidecar files from the server.",
)
async def delete_document_route(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
) -> dict:
    return await document_service.delete_document(document_id)


@router.post(
    "/{document_id}/extract",
    response_model=ExtractionMetadataResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract text from document",
    description="Parses the document, saves the extracted text as a sidecar JSON file, and returns extraction metadata.",
)
async def extract_document_text(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
) -> dict:
    return await document_service.extract_document(document_id)


@router.get(
    "/{document_id}/metadata",
    response_model=ExtractionMetadataResponse,
    summary="Get extraction metadata",
    description="Retrieves just the metadata of a previously extracted document.",
)
async def get_document_metadata(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
) -> dict:
    return await document_service.get_document_metadata(document_id)


@router.get(
    "/{document_id}/preview",
    response_model=ExtractionPreviewResponse,
    summary="Preview extracted text",
    description="Retrieves extraction metadata along with a truncated snippet of the parsed text.",
)
async def get_document_preview(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
) -> dict:
    return await document_service.get_document_preview(document_id)


@router.get(
    "/{document_id}/content",
    response_model=ExtractionContentResponse,
    summary="Get full extracted content",
    description="Retrieves the complete JSON payload containing the entire extracted document text.",
)
async def get_document_content(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
) -> dict:
    return await document_service.get_document_content(document_id)


# ---------------------------------------------------------------------------
# Phase 3 Analysis Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/{document_id}/analyze",
    response_model=AnalysisResultResponse,
    summary="Analyze extracted document",
    description=(
        "Runs the rule-based Financial Literacy analyzer on previously extracted text. "
        "Returns categorized topics, subtopics, difficulty rating, and learning objectives."
    ),
)
async def analyze_document(
    document_id: str,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> dict:
    return await analysis_service.analyze_document(document_id)


@router.get(
    "/{document_id}/analysis",
    response_model=AnalysisResultResponse,
    summary="Get document analysis",
    description="Retrieves the saved JSON sidecar resulting from a previous /analyze call.",
)
async def get_document_analysis(
    document_id: str,
    analysis_service: AnalysisService = Depends(get_analysis_service),
) -> dict:
    return await analysis_service.get_document_analysis(document_id)


# ---------------------------------------------------------------------------
# Phase 4 Question Generation Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/{document_id}/generate-questions",
    response_model=QuestionGenerationResponse,
    summary="Generate candidate questions",
    description=(
        "Uses the text extraction and analysis results to draft diagnostic candidate questions. "
        "Returns an array of structured Question Drafts mapped to specific misconceptions."
    ),
)
async def generate_questions(
    document_id: str,
    request: QuestionGenerationRequest,
    question_service: QuestionGenerationService = Depends(get_question_service),
    db: AsyncSession = Depends(get_db_session)
) -> dict:
    return await question_service.generate_questions(document_id, request, db)


@router.get(
    "/{document_id}/questions",
    response_model=QuestionGenerationResponse,
    summary="Get generated questions",
    description="Retrieves the saved JSON sidecar resulting from a previous /generate-questions call.",
)
async def get_document_questions(
    document_id: str,
    question_service: QuestionGenerationService = Depends(get_question_service),
) -> dict:
    return await question_service.get_document_questions(document_id)


@router.get(
    "/{document_id}/questions/{question_id}",
    response_model=QuestionDraft,
    summary="Get a specific question by ID",
    description="Retrieves an individual question object from the generated questions pool.",
)
async def get_question(
    document_id: str,
    question_id: str,
    question_service: QuestionGenerationService = Depends(get_question_service),
) -> dict:
    return await question_service.get_question_by_id(document_id, question_id)


