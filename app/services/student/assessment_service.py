import json
import logging
from typing import Dict, Any, List
from pathlib import Path

import aiofiles
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import Settings
from app.models.database_models import QuestionRecord, AnswerAttempt
from app.services.core.agents.grader_agent import GraderAgent

logger = logging.getLogger(__name__)

class AssessmentService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.grader = GraderAgent()

    async def get_quiz_questions(self, document_id: str, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Fetches approved questions for a document to be presented to a student.
        Hides the correct_answer and distractor_map to prevent cheating.
        """
        result = await db.execute(
            select(QuestionRecord).where(QuestionRecord.document_id == document_id)
        )
        records = result.scalars().all()
        
        if not records:
            # Fallback to sidecar if not in DB
            sidecar_path = self.settings.QUESTIONS_DIR / f"{document_id}_questions.json"
            if sidecar_path.exists():
                async with aiofiles.open(sidecar_path, "r", encoding="utf-8") as f:
                    data = json.loads(await f.read())
                    questions = data.get("questions", [])
            else:
                raise HTTPException(status_code=404, detail="No questions found for this document")
        else:
            questions = [r.payload for r in records]

        # Strip sensitive data for the student view
        student_questions = []
        for q in questions:
            sq = {
                "question_id": q.get("question_id"),
                "question_text": q.get("stem") or q.get("question_text"),
                "options": q.get("choices") or q.get("options", {}),
                "topic": q.get("topic"),
                "subtopic": q.get("subtopic"),
                "difficulty": q.get("difficulty")
            }
            student_questions.append(sq)
            
        return student_questions

    async def submit_answer(
        self, 
        document_id: str, 
        question_id: str, 
        selected_key: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Submits a student's answer and returns diagnostic feedback.
        """
        # 1. Fetch the full question payload (with correct answer and distractor map)
        result = await db.execute(
            select(QuestionRecord).where(
                QuestionRecord.document_id == document_id,
                QuestionRecord.id == question_id
            )
        )
        record = result.scalars().first()
        
        if not record:
            # Fallback to sidecar
            sidecar_path = self.settings.QUESTIONS_DIR / f"{document_id}_questions.json"
            if not sidecar_path.exists():
                raise HTTPException(status_code=404, detail="Question source not found")
            
            async with aiofiles.open(sidecar_path, "r", encoding="utf-8") as f:
                data = json.loads(await f.read())
                all_questions = data.get("questions", []) + data.get("pending_questions", [])
                payload = next((q for q in all_questions if q.get("question_id") == question_id), None)
        else:
            payload = record.payload

        if not payload:
            raise HTTPException(status_code=404, detail="Specific question not found")

        # 2. Grade using the Agent 4 (Grader)
        grader_output = self.grader.grade(payload, selected_key)

        # 3. Store the attempt in the database
        attempt = AnswerAttempt(
            question_id=question_id,
            user_id="anonymous_student",
            selected_choice_key=selected_key,
            is_correct=1 if grader_output.is_correct else 0
        )
        db.add(attempt)
        await db.commit()
        
        return grader_output.model_dump()
