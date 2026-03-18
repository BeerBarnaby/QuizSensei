from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.schemas.student.assessment import AnswerSubmissionRequest, AssessmentResponse
from app.services.student.assessment_service import AssessmentService

router = APIRouter(prefix="/assessment", tags=["assessment"])

def get_assessment_service(settings: Settings = Depends(get_settings)) -> AssessmentService:
    return AssessmentService(settings)

@router.get("/{document_id}/questions", response_model=List[dict])
async def get_quiz(
    document_id: str,
    service: AssessmentService = Depends(get_assessment_service),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Returns the list of questions for a student to answer.
    Sensitive data (correct answers) are stripped.
    """
    return await service.get_quiz_questions(document_id, db)

@router.post("/{document_id}/questions/{question_id}/submit", response_model=AssessmentResponse)
async def submit_answer(
    document_id: str,
    question_id: str,
    request: AnswerSubmissionRequest,
    service: AssessmentService = Depends(get_assessment_service),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Submits an answer and returns diagnostic feedback from Agent 4.
    """
    return await service.submit_answer(document_id, question_id, request.selected_key, db)
