"""
Service layer for question generation.
Orchestrates Agent 2 (Generator) and Agent 3 (Auditor) pipeline.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import aiofiles
from fastapi import HTTPException, status as fast_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.schemas.teacher.question import QuestionGenerationRequest
from app.services.core.generators.llm_question_generator import LLMQuestionGenerator
from app.services.core.agents.auditor_agent import AuditorAgent
from app.models.database_models import QuestionRecord

logger = logging.getLogger(__name__)


class QuestionGenerationService:
    """Orchestrates Agent 2 → Agent 3 pipeline with auto-regeneration."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.generator = LLMQuestionGenerator(settings)
        self.auditor   = AuditorAgent(settings)

    def _get_extracted_sidecar_path(self, document_id: str) -> Path:
        safe_id = Path(document_id).name
        return self.settings.EXTRACTED_DIR / f"{safe_id}.json"

    def _get_analysis_sidecar_path(self, document_id: str) -> Path:
        safe_id = Path(document_id).name
        return self.settings.ANALYSIS_DIR / f"{safe_id}_analysis.json"

    def _get_questions_sidecar_path(self, document_id: str) -> Path:
        safe_id = Path(document_id).name
        return self.settings.QUESTIONS_DIR / f"{safe_id}_questions.json"

    async def generate_questions(
        self,
        document_id: str,
        request: QuestionGenerationRequest,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Full pipeline with Regeneration Loop:
          1. Agent 2 generates needed amount of questions.
          2. Agent 3 audits them.
          3. If any rejected, loop back and ask Agent 2 to replace them (up to max_retries).
        """
        extracted_path = self._get_extracted_sidecar_path(document_id)
        if not extracted_path.exists():
            raise HTTPException(status_code=404, detail="Extraction data not found. Run /extract first.")

        analysis_path = self._get_analysis_sidecar_path(document_id)
        if not analysis_path.exists():
            raise HTTPException(status_code=404, detail="Analysis data not found. Run /analyze first.")

        try:
            async with aiofiles.open(extracted_path, "r", encoding="utf-8") as f:
                extraction_data = json.loads(await f.read())
            async with aiofiles.open(analysis_path, "r", encoding="utf-8") as f:
                analysis_data = json.loads(await f.read())
        except Exception:
            raise HTTPException(status_code=fast_status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Sidecar files unreadable.")

        # ── GATE: Content Sufficiency Check ────────────────────────────
        is_sufficient = analysis_data.get("content_sufficiency", False)
        if not is_sufficient and not request.additional_document_ids:
            msg = analysis_data.get("sufficiency_reason", "เนื้อหาไม่เพียงพอที่จะสร้างข้อสอบได้")
            rec = analysis_data.get("recommended_next_action", "กรุณาอัปโหลดเอกสารที่มีเนื้อหาทางการเงินดรายอื่นเพิ่มเติม")
            logger.warning(f"Generation blocked for {document_id}: {msg}")
            raise HTTPException(
                status_code=fast_status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"ระบบหยุดการสร้างข้อสอบ: {msg} ({rec})"
            )

        text = extraction_data.get("extracted_text", "")

        # ── Merge additional docs ───────────────────────────────────────
        for extra_id in (request.additional_document_ids or []):
            extra_path = self._get_extracted_sidecar_path(extra_id)
            if extra_path.exists():
                try:
                    async with aiofiles.open(extra_path, "r", encoding="utf-8") as f:
                        extra_data = json.loads(await f.read())
                    extra_text = extra_data.get("extracted_text", "")
                    if extra_text:
                        text += f"\n\n--- เอกสารเพิ่มเติม ({extra_id}) ---\n\n" + extra_text
                        logger.info(f"Merged extra doc: {extra_id}")
                except Exception as e:
                    logger.warning(f"Could not read extra doc {extra_id}: {e}")

        target_amount = request.number_of_questions
        audience = request.target_audience_level
        difficulty = request.difficulty_filter or "ปานกลาง"

        approved_questions: List[Dict] = []
        rejected_questions: List[Dict] = []
        pending_questions: List[Dict] = []
        
        max_attempts = 3
        attempts = 0

        # ── REGENERATION LOOP ───────────────────────────────────────────
        # This loop ensures we meet the user's requested 'target_amount' of 
        # questions that have been officially APPROVED by Agent 3 (Auditor).
        while len(approved_questions) < target_amount and attempts < max_attempts:
            needed = target_amount - len(approved_questions)
            logger.info(f"Loop {attempts+1}/{max_attempts}: Generating {needed} questions...")
            
            # Request only the missing delta from Agent 2
            loop_req = request.model_copy(update={"number_of_questions": needed})
            
            try:
                raw_drafts = await self.generator.generate(text, analysis_data, loop_req)
            except Exception as e:
                logger.error(f"Generate fail: {e}")
                break

            try:
                # Agent 3 (Auditor) verifies if the drafts meet quality standards
                audited = await self.auditor.audit(raw_drafts, audience, difficulty)
            except Exception as e:
                logger.error(f"Audit fail: {e}")
                # If audit fails, we keep the drafts but they remain 'pending'
                pending_questions.extend(raw_drafts)
                break

            for q in audited:
                q_status = q.get("audit_status")
                if q_status == "approved":
                    approved_questions.append(q)
                elif q_status == "rejected":
                    rejected_questions.append(q)
                else:
                    pending_questions.append(q)

            attempts += 1

        # Truncate if we accidentally generated more than target due to batching
        if len(approved_questions) > target_amount:
            approved_questions = approved_questions[:target_amount]

        result = {
            "document_id": document_id,
            "generation_status": "success",
            "questions": approved_questions,
            "rejected_questions": rejected_questions,
            "pending_questions": pending_questions,
            "total_generated": len(approved_questions) + len(rejected_questions) + len(pending_questions),
            "total_approved": len(approved_questions),
            "total_rejected": len(rejected_questions),
            "message": f"ใช้รอบการสร้าง {attempts} รอบ ได้ {len(approved_questions)} ข้อ",
        }

        # ── Persist sidecar JSON ─────────────────────────
        questions_path = self._get_questions_sidecar_path(document_id)
        async with aiofiles.open(questions_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(result, ensure_ascii=False, indent=2))

        # ── Persist APPROVED to PostgreSQL ───────────────────
        for q in approved_questions:
            db_record = QuestionRecord(
                id=q["question_id"],
                document_id=document_id,
                topic=q.get("topic", "unknown"),
                subtopic=q.get("subtopic", "unknown"),
                difficulty=q.get("difficulty", "unknown"),
                payload=q,
            )
            await db.merge(db_record)
        if approved_questions:
            await db.commit()

        return result

    async def get_document_questions(self, document_id: str) -> Dict[str, Any]:
        """Retrieves the saved questions sidecar."""
        path = self._get_questions_sidecar_path(document_id)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Questions not found.")
        async with aiofiles.open(path, "r", encoding="utf-8") as f:
            return json.loads(await f.read())

    async def get_question_by_id(self, document_id: str, question_id: str) -> Dict[str, Any]:
        """Retrieves a specific question from the sidecar."""
        full = await self.get_document_questions(document_id)
        for list_name in ["questions", "rejected_questions", "pending_questions"]:
            for q in full.get(list_name, []):
                if q.get("question_id") == question_id:
                    return q
        raise HTTPException(status_code=404, detail="Question not found.")
