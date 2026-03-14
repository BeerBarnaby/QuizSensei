"""
app/schemas/exam.py

Pydantic schemas for the Exam & Analytics endpoints.
SubmissionResult now carries Agent 4 (Grader) diagnostic output.
"""

from typing import Optional
from pydantic import BaseModel, Field


class AnswerSubmission(BaseModel):
    """Payload received from the frontend when a user answers a question."""
    question_id: str = Field(..., description="ID of the question being answered.")
    selected_choice_key: str = Field(..., description="Choice key selected by the user (e.g. 'A').")
    user_id: Optional[str] = Field(None, description="Optional anonymous/session user ID.")


class SubmissionResult(BaseModel):
    """
    Response returned after submitting an answer.
    Enriched with Agent 4 (Grader) diagnostic output.
    """
    question_id: str
    is_correct: bool
    correct_answer: str
    # Agent 4 outputs
    misconception_identified: Optional[str] = Field(
        None,
        description="Specific misconception name if the student answered incorrectly."
    )
    diagnostic_message: str = Field(
        ...,
        description="Personalized, educationally rich explanation from Agent 4."
    )
    suggested_review_topic: Optional[str] = Field(
        None,
        description="FL subtopic the student should review."
    )
    message: str = Field(..., description="Short summary message.")


class QuestionAnalytics(BaseModel):
    """Analytics payload for a specific question including empirical difficulty (p-value)."""
    question_id: str
    total_attempts: int
    correct_attempts: int
    p_value: float = Field(..., description="Difficulty Index: correct / total (0.0 to 1.0)")
    empirical_difficulty: str = Field(..., description="Hard / Medium / Easy based on p-value")
