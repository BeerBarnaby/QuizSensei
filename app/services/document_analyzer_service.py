"""
app/services/document_analyzer_service.py

Service layer for orchestrating the analysis of extracted documents.
Loads the document from the JSON sidecar created during Phase 2,
runs the configured analyzer, and saves the new analysis JSON sidecar.
"""

import json
from pathlib import Path
from typing import Dict, Any

import aiofiles
from fastapi import HTTPException, status

from app.core.config import Settings
from app.services.analyzers.rule_based_analyzer import RuleBasedAnalyzer

class DocumentAnalyzerService:
    """Provides business logic for running analysis on extracted documents."""

    def __init__(self, settings: Settings):
        self.settings = settings
        # In the future, this could be instantiated dynamically based on environment var or DB config
        # e.g., if settings.USE_LLM_ANALYZER: self.analyzer = OpenRouterAnalyzer(...)
        self.analyzer = RuleBasedAnalyzer()

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
        Main pipeline: Validates extraction exists -> Runs analysis -> Saves sidecar.
        """
        # 1. Verify document has been extracted
        extracted_path = self._get_extracted_sidecar_path(document_id)
        if not extracted_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Extraction data not found. Please run the /extract endpoint first."
            )

        # 2. Load the extracted text
        async with aiofiles.open(extracted_path, "r", encoding="utf-8") as f:
            extraction_data = json.loads(await f.read())

        text = extraction_data.get("extracted_text")
        
        # Handle cases where extraction failed (e.g. .doc format or corrupted file)
        if not text:
             return await self._save_and_return_failed_status(
                 document_id, "Cannot analyze document: no extracted text available. Did the extraction fail?"
             )

        # 3. Execute Analysis Strategy
        try:
            analysis_dict = await self.analyzer.analyze(text)
            
            result = {
                "document_id": document_id,
                "status": "success",
                "topic": analysis_dict.get("topic"),
                "subtopic": analysis_dict.get("subtopic"),
                "difficulty": analysis_dict.get("difficulty"),
                "learning_objective_candidate": analysis_dict.get("learning_objective_candidate"),
                "keywords_found": analysis_dict.get("keywords_found", []),
                "rationale": analysis_dict.get("rationale"),
                "message": None
            }
        except Exception as e:
            # Catch unexpected analyzer breaks
            return await self._save_and_return_failed_status(
                document_id, f"Analysis failed internally: {str(e)}"
            )

        # 4. Persist Analysis result
        analysis_path = self._get_analysis_sidecar_path(document_id)
        self.settings.ensure_upload_dir() # safeguard to ensure directories exist

        async with aiofiles.open(analysis_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(result, ensure_ascii=False, indent=2))

        return result

    async def _save_and_return_failed_status(self, document_id: str, message: str) -> Dict[str, Any]:
        """Helper to return and persist a failed analysis state."""
        result = {
            "document_id": document_id,
            "status": "failed",
            "topic": None,
            "subtopic": None,
            "difficulty": None,
            "learning_objective_candidate": None,
            "keywords_found": [],
            "rationale": None,
            "message": message
        }
        
        analysis_path = self._get_analysis_sidecar_path(document_id)
        self.settings.ensure_upload_dir()
        
        async with aiofiles.open(analysis_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(result, indent=2))
            
        # Fast fail response
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result
        )

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
