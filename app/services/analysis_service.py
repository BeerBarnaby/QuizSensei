"""
Service layer for document analysis.
Coordinates extraction data with Agent 1 (Analyzer).
"""

import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

import aiofiles
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.services.analyzer_service import LLMDocumentAnalyzer

class AnalysisService:
    """Provides business logic for running analysis on extracted documents."""

    def __init__(self, settings: Settings, document_service: Any = None):
        self.settings = settings
        self.document_service = document_service
        # Swapped to generic LLM analyzer for domain-agnostic assessment
        self.analyzer = LLMDocumentAnalyzer(settings)

    async def _get_extracted_sidecar_path(self, document_id: str, db: Optional[AsyncSession] = None) -> Path:
        """
        Returns the path of the Phase 2 extraction JSON.
        Uses DocumentService's polymorphic resolution.
        """
        return await self.document_service._get_sidecar_path(document_id, db=db)

    async def _get_analysis_sidecar_path(self, document_id: str, db: Optional[AsyncSession] = None) -> Path:
        """
        Returns the path where the Phase 3 analysis JSON is stored.
        Polymorphic: supports both UUID and filename-based sidecars.
        """
        # 1. Direct check
        safe_id = Path(document_id).name
        analysis_path = self.settings.ANALYSIS_DIR / f"{safe_id}_analysis.json"
        
        if analysis_path.exists():
            return analysis_path
            
        # 2. DB Resolve (UUID to Filename)
        if db:
            try:
                from sqlalchemy import select
                from app.models.document import Document
                import uuid
                try:
                    u = uuid.UUID(document_id)
                    query = select(Document).where(Document.id == u)
                    res = await db.execute(query)
                    doc = res.scalar_one_or_none()
                    if doc:
                        filename_stem = Path(doc.storage_path).name
                        alt_path = self.settings.ANALYSIS_DIR / f"{filename_stem}_analysis.json"
                        if alt_path.exists():
                            return alt_path
                except ValueError:
                    pass
            except Exception:
                pass

        return analysis_path

    async def analyze_document(self, document_id: str, db: Optional[Any] = None) -> Dict[str, Any]:
        """
        Main pipeline: Validates extraction exists -> Runs analysis -> Saves analysis sidecar.
        """
        from app.models.document import Document
        from sqlalchemy.future import select
        from app.core.llm import logger

        # 1. Verify document has been extracted
        extracted_path = await self._get_extracted_sidecar_path(document_id, db=db)
        if not extracted_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis data not found. Please run the /extract endpoint first."
            )

        # 2. Load the extracted text
        try:
            async with aiofiles.open(extracted_path, "r", encoding="utf-8") as f:
                extraction_data = json.loads(await f.read())
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Extraction sidecar is unreadable or corrupted."
            )

        text = extraction_data.get("extracted_text")
        filename = extraction_data.get("filename", document_id)
        
        # 3. Guard against empty text
        if not text or len(text.strip()) == 0:
             return await self._save_and_return_failed_status(
                 document_id, filename, "Cannot analyze document: no extracted text available. Did the extraction fail?"
             )

        # 4. Execute Analysis Strategy
        try:
            analysis_dict = await self.analyzer.analyze(text)
            
            # Map analyzer dict to exact output fields
            result = {
                "document_id": document_id,
                "filename": filename,
                "analysis_status": "success",
                "topic": analysis_dict.get("topic"),
                "subtopic": analysis_dict.get("subtopic"),
                "suggested_learner_level": analysis_dict.get("suggested_learner_level"),
                "learner_level_reason": analysis_dict.get("learner_level_reason"),
                "content_sufficiency": analysis_dict.get("content_sufficiency", False),
                "sufficiency_reason": analysis_dict.get("sufficiency_reason"),
                "should_upload_more_documents": analysis_dict.get("should_upload_more_documents", True),
                "recommended_next_action": analysis_dict.get("recommended_next_action"),
                "status": analysis_dict.get("status", "success"),
                "message": analysis_dict.get("message", "Analysis completed successfully."),
                "keywords_found": analysis_dict.get("keywords_found", []),
                "indicators": analysis_dict.get("indicators", []),
                "analyzed_char_count": analysis_dict.get("analyzed_char_count", 0),
            }
        except Exception as e:
            # Catch unexpected internal breaks (e.g. regex failure)
            return await self._save_and_return_failed_status(
                document_id, filename, f"กระบวนการวิเคราะห์ล้มเหลว: {str(e)}"
            )

        # 5. Persist Analysis result
        analysis_path = await self._get_analysis_sidecar_path(document_id, db=db)

        async with aiofiles.open(analysis_path, "w", encoding="utf-8") as f:
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
                    query = select(Document).where(Document.storage_path.like(f"%{document_id}"))
                    db_res = await db.execute(query)
                    db_doc = db_res.scalar_one_or_none()

                if db_doc:
                    db_doc.extraction_state = "analyzed"
                    await db.commit()
                else:
                    logger.warning(f"DB Update (Analysis): Document record not found for {document_id}")
            except Exception as de:
                logger.error(f"Failed to update analysis state in DB: {de}")

        return result

    async def _save_and_return_failed_status(self, document_id: str, filename: str, message: str, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """Helper to safely format and persist a failed analysis state."""
        result = {
            "document_id": document_id,
            "filename": filename,
            "analysis_status": "failed",
            "topic": None,
            "subtopic": None,
            "suggested_learner_level": None,
            "learner_level_reason": None,
            "content_sufficiency": False,
            "sufficiency_reason": message,
            "should_upload_more_documents": True,
            "recommended_next_action": "Please check the document and upload again.",
            "status": "failed",
            "message": message,
            "keywords_found": [],
            "indicators": [],
            "analyzed_char_count": 0,
        }
        
        analysis_path = await self._get_analysis_sidecar_path(document_id, db=db)
        
        async with aiofiles.open(analysis_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(result, ensure_ascii=False, indent=2))
            
        return result

    async def get_document_analysis(self, document_id: str, db: Optional[AsyncSession] = None) -> Dict[str, Any]:
        """Retrieves an existing analysis sidecar file using polymorphic resolution."""
        analysis_path = await self._get_analysis_sidecar_path(document_id, db=db)
        if not analysis_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Analysis data not found. Please run the /analyze endpoint first."
            )

        async with aiofiles.open(analysis_path, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content)
