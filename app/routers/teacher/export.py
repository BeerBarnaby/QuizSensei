from fastapi import APIRouter, Depends, HTTPException, Response
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db_session
from app.models.database_models import QuestionRecord
from app.services.teacher.export_service import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])
export_service = ExportService()

@router.get("/{document_id}/moodle")
async def export_moodle(document_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Exports all approved questions for a document in Moodle XML format.
    """
    result = await db.execute(
        select(QuestionRecord).where(QuestionRecord.document_id == document_id)
    )
    questions = result.scalars().all()
    
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this document")

    # Extract payloads for the service
    payloads = [q.payload for q in questions]
    
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
        select(QuestionRecord).where(QuestionRecord.document_id == document_id)
    )
    questions = result.scalars().all()
    
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found for this document")

    payloads = [q.payload for q in questions]
    return export_service.export_to_json_standard(payloads)
