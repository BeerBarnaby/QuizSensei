"""
Pydantic schemas for structured AI agent outputs.
Includes models for Analyzer, Auditor, and Grader agents in the pipeline.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AnalyzerOutput(BaseModel):
    """Structured output from Agent 1 (Financial Literacy Analyzer)."""
    document_id: str = Field(..., description="ID of the analyzed document.")
    topic: Optional[str] = Field(None, description="Financial Literacy main topic slug.")
    subtopic: Optional[str] = Field(None, description="Specific FL sub-topic slug.")
    suggested_learner_level: Optional[str] = Field(
        None, 
        description="Target audience level: 'ประถม', 'มัธยมต้น', 'มัธยมปลาย', 'มหาวิทยาลัย', 'วัยทำงาน'."
    )
    learner_level_reason: Optional[str] = Field(None, description="Reason for the selected learner level in Thai.")
    content_sufficiency: bool = Field(False, description="True if content is sufficient to generate questions, False otherwise.")
    sufficiency_reason: Optional[str] = Field(None, description="Explanation of why content is sufficient or not in Thai.")
    should_upload_more_documents: bool = Field(True, description="True if the user needs to upload more content.")
    recommended_next_action: Optional[str] = Field(None, description="Suggested next step for the user in Thai.")
    status: str = Field(default="success", description="Status of the analysis ('success' or 'failed').")
    message: Optional[str] = Field(default="วิเคราะห์เสร็จสมบูรณ์", description="System message to the user in Thai.")
    keywords_found: list[str] = Field(default_factory=list)
    analyzed_char_count: int = Field(0)


class AuditResult(BaseModel):
    """Structured output from Agent 3 (Auditor) for a single question."""
    question_id: str
    audit_status: str = Field(..., description="'approved' or 'rejected'.")
    audit_feedback: Optional[str] = Field(
        None,
        description="Explanation of what was wrong (if rejected) or what makes this question strong (if approved)."
    )
    checked_at: datetime = Field(default_factory=datetime.utcnow)


class GraderOutput(BaseModel):
    """Structured output from Agent 4 (Grader) after a student submits an answer."""
    question_id: str
    is_correct: bool
    correct_answer: str
    misconception_identified: Optional[str] = Field(
        None,
        description="Specific misconception name if the student answered incorrectly."
    )
    diagnostic_message: str = Field(
        ...,
        description="A personalized, educationally rich explanation for the student."
    )
    suggested_review_topic: Optional[str] = Field(
        None,
        description="FL sub-topic the student should review based on their answer."
    )
