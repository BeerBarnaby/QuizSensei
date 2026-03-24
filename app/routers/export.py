from fastapi import APIRouter, Depends, HTTPException, Response
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db_session
from app.models.question import Question
from app.services.export_service import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])
export_service = ExportService()

@router.get("/{document_id}/moodle")
async def export_moodle(document_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Exports all approved questions for a document in Moodle XML format.
    """
    result = await db.execute(
        select(Question).where(Question.quiz_id == document_id)
    )
    questions = result.scalars().all()
    
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this document")

    # Extract payloads/attributes for the service
    payloads = []
    for q in questions:
        # Construct a payload format that the ExportService expects
        payloads.append({
            "id": str(q.id),
            "stem": q.stem_th,
            "choices": [{"key": c.choice_key, "text": c.choice_text_th} for c in q.choices],
            "correct_answer": q.correct_answer_key,
            "rationale_for_correct_answer": q.rationale_correct_th,
            "distractor_map": q.distractor_map or {}
        })
    
    xml_content = export_service.export_to_moodle_xml(payloads, category_name=f"QuizSensei_{document_id}")
    
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={
            "Content-Disposition": f"attachment; filename=quiz_sensei_{document_id}.xml"
        }
    )

@router.get("/{document_id}/json")
async def export_json(document_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Exports all approved questions for a document in standard JSON format.
    """
    result = await db.execute(
        select(Question).where(Question.quiz_id == document_id)
    )
    questions = result.scalars().all()
    
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this document")

    payloads = []
    for q in questions:
        payloads.append({
            "id": str(q.id),
            "stem": q.stem_th,
            "choices": [{"key": c.choice_key, "text": c.choice_text_th} for c in q.choices],
            "correct_answer": q.correct_answer_key,
            "rationale_for_correct_answer": q.rationale_correct_th,
            "distractor_map": q.distractor_map or {}
        })
    return export_service.export_to_json_standard(payloads)
