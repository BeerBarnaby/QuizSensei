"""
app/schemas/question.py

Pydantic schemas for Phase 4 Question Generation endpoints.
Questions now include Agent 2 (design_reasoning, distractor_map)
and Agent 3 (audit_status, audit_feedback) fields.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Choice(BaseModel):
    """A single option for a multiple-choice question."""
    key: str = Field(..., description="e.g., 'A', 'B', 'C', 'D'")
    text: str = Field(..., description="The text of the choice.")


class QuestionGenerationRequest(BaseModel):
    """Payload to request question generation with optional filters."""
    number_of_questions: int = Field(default=3, ge=1, le=10)
    target_audience_level: str = Field(
        default="วัยทำงาน",
        description="Target audience: 'ประถมศึกษา', 'มัธยมศึกษาตอนต้น', 'มัธยมศึกษาตอนปลาย', 'อุดมศึกษา', 'วัยทำงาน'"
    )
    difficulty_filter: Optional[str] = Field(None, description="easy | medium | hard")
    topic_filter: Optional[str] = Field(None, description="Force a specific FL topic.")
    subtopic_filter: Optional[str] = Field(None, description="Force a specific FL subtopic.")
    additional_document_ids: List[str] = Field(
        default_factory=list,
        description="Extra document IDs whose extracted text will be merged with the primary document."
    )


class QuestionDraft(BaseModel):
    """A single generated candidate question — enriched with Agent 2 & 3 outputs."""
    question_id: str
    topic: str
    subtopic: str
    target_audience_level: str = Field(..., description="The audience level this question was designed for.")
    difficulty: str
    question_type: str = Field("multiple_choice")

    stem: str
    choices: List[Choice]
    correct_answer: str

    rationale_for_correct_answer: str
    rationale_for_incorrect_choices: str

    # ── Agent 2 deep justification ───────────────────────────────────────
    design_reasoning: Optional[str] = Field(
        None,
        description="Agent 2: WHY this question is pedagogically needed for FL education."
    )
    distractor_map: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Agent 2: Per-distractor analysis. "
            "Keys are wrong choice keys (e.g. 'A'). "
            "Values: {misconception, why_plausible, diagnostic_meaning, suggested_review_topic}."
        )
    )
    misconception_tags: List[str] = Field(default_factory=list)

    source_evidence: Optional[str] = Field(None)
    why_this_question: Optional[str] = Field(None)

    # ── Agent 3 audit fields ─────────────────────────────────────────────
    audit_status: str = Field("pending", description="'pending' | 'approved' | 'rejected'")
    audit_feedback: Optional[str] = Field(None, description="Agent 3 feedback.")

    status: str = Field("draft", description="'draft' | 'approved' | 'rejected'")


class QuestionGenerationResponse(BaseModel):
    """Response model for /generate-questions endpoint."""
    document_id: str
    generation_status: str
    questions: List[QuestionDraft] = Field(default_factory=list, description="APPROVED questions only.")
    rejected_questions: List[QuestionDraft] = Field(default_factory=list)
    pending_questions: List[QuestionDraft] = Field(default_factory=list)
    total_generated: int = Field(0)
    total_approved: int = Field(0)
    total_rejected: int = Field(0)
    message: Optional[str] = None
