"""
Service layer for document management.
Orchestrates file storage, extraction strategies, and cleanup.
"""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

import aiofiles
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.services.core.extractors.txt_extractor import TxtExtractor
from app.services.core.extractors.pdf_extractor import PDFExtractor
from app.services.core.extractors.docx_extractor import DocxExtractor


class DocumentService:
    """Provides business logic for managing, extracting, and previewing documents."""

    def __init__(self, settings: Settings):
        self.settings = settings

        # Strategy map for extractors based on file extension
        self.extractors = {
            ".txt": TxtExtractor(),
            ".pdf": PDFExtractor(),
            ".docx": DocxExtractor(),
        }

    def _get_document_path(self, document_id: str) -> Path:
        """Returns bounds-safe path to the uploaded document."""
        # Note: In Phase 1 we already sanitised the filename during upload.
        # But we must ensure users cannot pass paths like ../../ in document_id.
        safe_id = Path(document_id).name
        return self.settings.UPLOAD_DIR / safe_id

    def _get_sidecar_path(self, document_id: str) -> Path:
        """Returns the path where the JSON extraction result will be stored."""
        safe_id = Path(document_id).name
        sidecar_path = self.settings.EXTRACTED_DIR / f"{safe_id}.json"
        
        # Log path for troubleshooting 404
        from app.core.llm import logger
        logger.info(f"Checking sidecar path: {sidecar_path} (exists: {sidecar_path.exists()})")
        
        return sidecar_path

    async def extract_document(self, document_id: str, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """
        Extracts content from a document using the appropriate strategy and
        saves a JSON sidecar file containing metadata + full text.
        Returns the metadata dict (without full text) to the caller.
        """
        from app.core.llm import logger
        from app.models.document import Document
        from sqlalchemy.future import select

        logger.info(f"--- START EXTRACTION for {document_id} ---")
        
        doc_path = self._get_document_path(document_id)
        if not doc_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found."
            )

        ext = doc_path.suffix.lower()

        # Handle unsupported files gracefully without throwing 500s
        if ext == ".doc":
            return await self._save_and_return_failed_result(
                document_id, ext, "Parsing not supported for .doc files yet."
            )
            
        if ext not in self.extractors:
            return await self._save_and_return_failed_result(
                document_id, ext, f"No extractor available for {ext}."
            )

        extractor = self.extractors[ext]
        
        try:
            # Execute strategy
            extracted_text = await extractor.extract_text(doc_path)
            
            # Prepare result dictionary
            result = {
                "document_id": document_id,
                "filename": document_id, # Can be enhanced in DB phase
                "extension": ext,
                "extraction_status": "success",
                "char_count": len(extracted_text),
                "extracted_text": extracted_text,
                "message": None
            }
        except Exception as e:
            # Extraction failure (bad encoding, corrupted PDF, etc.)
            return await self._save_and_return_failed_result(
                document_id, ext, f"Extraction failed: {str(e)}"
            )

        # Persist sidecar JSON
        sidecar_path = self._get_sidecar_path(document_id)
        
        async with aiofiles.open(sidecar_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(result, ensure_ascii=False, indent=2))

        # ── Update Database State ──────────────────────────────────────────
        if db:
            try:
                # 1. Attempt lookup by UUID (Preferred)
                db_doc = None
                try:
                    target_uuid = uuid.UUID(document_id)
                    query = select(Document).where(Document.id == target_uuid)
                    db_res = await db.execute(query)
                    db_doc = db_res.scalar_one_or_none()
                except (ValueError, AttributeError):
                    # Not a UUID, fallback to Filename/StoragePath lookup
                    pass

                # 2. Fallback lookup by storage_path suffix
                if not db_doc:
                    # Search for documents where storage_path contains the filename
                    # document_id here is something like 'dcf592ba_document.txt'
                    query = select(Document).where(Document.storage_path.like(f"%{document_id}"))
                    db_res = await db.execute(query)
                    db_doc = db_res.scalar_one_or_none()

                if db_doc:
                    db_doc.extraction_state = "extracted"
                    await db.commit()
                else:
                    logger.warning(f"DB Update: Document record not found for {document_id}")
            except Exception as de:
                logger.error(f"Failed to update extraction state in DB: {de}")
        
        logger.info(f"--- EXTRACTION COMPLETE for {document_id} ({len(extracted_text)} chars) ---")
        return self._strip_text(result)

    async def _save_and_return_failed_result(self, document_id: str, ext: str, message: str) -> Dict[str, Any]:
        """Helper to return and persist a failed extraction state."""
        result = {
            "document_id": document_id,
            "filename": document_id,
            "extension": ext,
            "extraction_status": "failed",
            "char_count": 0,
            "extracted_text": None,
            "message": message
        }
        sidecar_path = self._get_sidecar_path(document_id)
        async with aiofiles.open(sidecar_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(result, indent=2))
        return self._strip_text(result)

    def _strip_text(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Returns a copy of the dict with the heavy extracted_text removed."""
        metadata = result.copy()
        metadata.pop("extracted_text", None)
        return metadata

    async def get_document_content(self, document_id: str) -> Dict[str, Any]:
        """Returns the full JSON containing metadata and all extracted_text."""
        sidecar_path = self._get_sidecar_path(document_id)
        if not sidecar_path.exists():
            from app.core.llm import logger
            logger.error(f"Sidecar file NOT FOUND: {sidecar_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Extraction data not found for {document_id}. Please extract it first."
            )

        async with aiofiles.open(sidecar_path, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content)

    async def get_document_preview(self, document_id: str, max_chars: int = 500) -> Dict[str, Any]:
        """Returns metadata + a truncated preview snippet of the extracted_text."""
        full_content = await self.get_document_content(document_id)
        
        preview_text = None
        if full_content.get("extracted_text"):
            preview_text = full_content["extracted_text"][:max_chars]
            if len(full_content["extracted_text"]) > max_chars:
                preview_text += "..."

        return {
            "document_id": full_content["document_id"],
            "filename": full_content["filename"],
            "extension": full_content["extension"],
            "extraction_status": full_content["extraction_status"],
            "char_count": full_content["char_count"],
            "preview_text": preview_text,
            "message": full_content["message"]
        }

    async def get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """Returns just the metadata stats of a past extraction."""
        full_content = await self.get_document_content(document_id)
        return self._strip_text(full_content)

    async def delete_document(self, document_id: str) -> Dict[str, str]:
        """
        Deletes the uploaded document and all associated sidecar files (extraction, analysis, questions).
        Returns a status dictionary.
        """
        safe_id = Path(document_id).name
        
        # Paths to specific user files
        doc_path = self._get_document_path(safe_id)
        extraction_path = self._get_sidecar_path(safe_id)
        analysis_path = self.settings.ANALYSIS_DIR / f"{safe_id}_analysis.json"
        questions_path = self.settings.QUESTIONS_DIR / f"{safe_id}_questions.json"
        
        # Check if the primary document exists
        if not doc_path.exists():
             raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found."
            )

        # Unlink all related files without throwing errors if generated ones are missing
        for path in [doc_path, extraction_path, analysis_path, questions_path]:
            if path.exists():
                try:
                    path.unlink()
                except OSError as e:
                    # In a production app, log this error instead of failing silently on sidecars
                    pass

        return {"status": "success", "message": f"Document '{safe_id}' and its related files have been deleted"}

