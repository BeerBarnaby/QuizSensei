"""
Service layer for orchestrating document analysis (Phase 3).
Connects extraction results to the Financial Literacy analyzer and manages analysis sidecars.
"""

import json
from pathlib import Path
from typing import Dict, Any

import aiofiles
from fastapi import HTTPException, status

from app.core.config import Settings
from app.services.analyzers.llm_financial_literacy_analyzer import LLMFinancialLiteracyAnalyzer

class AnalysisService:
    """Provides business logic for running analysis on extracted documents."""

    def __init__(self, settings: Settings):
        self.settings = settings
        # Swapped to LLM analyzer as requested
        self.analyzer = LLMFinancialLiteracyAnalyzer(settings)

    def _get_extracted_sidecar_path(self, document_id: str) -> Path:
        """Returns the path of the Phase 2 extraction JSON."""
        safe_id = Path(document_id).name
        return self.settings.EXTRACTED_DIR / f"{safe_id}.json"

    def _get_analysis_sidecar_path(self, document_id: str) -> Path:
        """Returns the path where the Phase 3 analysis JSON will be stored."""
        safe_id = Path(document_id).name
        return self.settings.ANALYSIS_DIR / f"{safe_id}_analysis.json"

    async def analyze_document(self, document_id: str) -> Dict[str, Any]:
        """
        Main pipeline: Validates extraction exists -> Runs analysis -> Saves analysis sidecar.
        """
        # 1. Verify document has been extracted
        extracted_path = self._get_extracted_sidecar_path(document_id)
        if not extracted_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Extraction data not found. Please run the /extract endpoint first."
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
                "message": analysis_dict.get("message", "วิเคราะห์สำเร็จ"),
                "keywords_found": analysis_dict.get("keywords_found", []),
                "analyzed_char_count": analysis_dict.get("analyzed_char_count", 0),
            }
        except Exception as e:
            # Catch unexpected internal breaks (e.g. regex failure)
            return await self._save_and_return_failed_status(
                document_id, filename, f"กระบวนการวิเคราะห์ล้มเหลว: {str(e)}"
            )

        # 5. Persist Analysis result
        analysis_path = self._get_analysis_sidecar_path(document_id)

        async with aiofiles.open(analysis_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(result, ensure_ascii=False, indent=2))

        return result

    async def _save_and_return_failed_status(self, document_id: str, filename: str, message: str) -> Dict[str, Any]:
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
            "recommended_next_action": "กรุณาตรวจสอบเอกสารและอัปโหลดใหม่",
            "status": "failed",
            "message": message,
            "keywords_found": [],
            "analyzed_char_count": 0,
        }
        
        analysis_path = self._get_analysis_sidecar_path(document_id)
        
        async with aiofiles.open(analysis_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(result, indent=2))
            
        return result

    async def get_document_analysis(self, document_id: str) -> Dict[str, Any]:
        """Retrieves an existing analysis sidecar file."""
        analysis_path = self._get_analysis_sidecar_path(document_id)
        if not analysis_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Analysis data not found. Please run the /analyze endpoint first."
            )

        async with aiofiles.open(analysis_path, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content)
