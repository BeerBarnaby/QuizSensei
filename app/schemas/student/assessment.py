from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AnswerSubmissionRequest(BaseModel):
    selected_key: str = Field(..., description="The student's choice (A, B, C, or D)")

class AssessmentResponse(BaseModel):
    question_id: str
    is_correct: bool
    correct_answer: str
    misconception_identified: Optional[str] = None
    diagnostic_message: str
    suggested_review_topic: Optional[str] = None
