"""
app/routers/exams.py

Exam & Analytics router.
POST /exams/submit now uses Agent 4 (GraderAgent) for diagnostic grading.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.db.session import get_db_session
from app.models.database_models import QuestionRecord, AnswerAttempt
from app.schemas.exam import AnswerSubmission, SubmissionResult, QuestionAnalytics
from app.services.agents.grader_agent import GraderAgent

router = APIRouter(prefix="/exams", tags=["Exams & Analytics"])

# Singleton grader (stateless, no LLM needed)
_grader = GraderAgent()


@router.post(
    "/submit",
    response_model=SubmissionResult,
    summary="Submit an answer to a question (Agent 4: Grader)",
    description=(
        "Grades the student's answer using Agent 4 (GraderAgent). "
        "Returns is_correct, the specific misconception identified, "
        "a personalized diagnostic message, and a suggested review topic."
    ),
)
async def submit_answer(
    submission: AnswerSubmission,
    db: AsyncSession = Depends(get_db_session),
):
    # ── 1. Fetch the question from DB ─────────────────────────────────────
    result = await db.execute(
        select(QuestionRecord).where(QuestionRecord.id == submission.question_id)
    )
    question_record = result.scalars().first()

    if not question_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found in database.",
        )

    # ── 2. Run Agent 4 (Grader) ───────────────────────────────────────────
    grader_output = _grader.grade(
        question_payload=question_record.payload,
        selected_key=submission.selected_choice_key,
    )

    # ── 3. Record the attempt for analytics ──────────────────────────────
    attempt = AnswerAttempt(
        question_id=submission.question_id,
        user_id=submission.user_id,
        selected_choice_key=submission.selected_choice_key.upper(),
        is_correct=1 if grader_output.is_correct else 0,
    )
    db.add(attempt)
    await db.commit()

    # ── 4. Return enriched result ─────────────────────────────────────────
    return SubmissionResult(
        question_id=grader_output.question_id,
        is_correct=grader_output.is_correct,
        correct_answer=grader_output.correct_answer,
        misconception_identified=grader_output.misconception_identified,
        diagnostic_message=grader_output.diagnostic_message,
        suggested_review_topic=grader_output.suggested_review_topic,
        message="ถูกต้อง! ยอดเยี่ยมมาก 🎉" if grader_output.is_correct else "ไม่ถูกต้อง ลองทบทวนดูนะ 📖",
    )


