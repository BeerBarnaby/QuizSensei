"""
Pydantic schemas for document analysis results.
Defines the final structured outcome of the Phase 3 analysis process.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

class AnalysisResultResponse(BaseModel):
    """
    Response model for document analysis results.
    Matches the updated Agent 1 output exactly.
    """
    document_id: str = Field(..., description="The ID (filename) of the extracted document.")
    topic: Optional[str] = Field(None, description="The primary Financial Literacy category.")
    subtopic: Optional[str] = Field(None, description="The specific subtopic within the category.")
    suggested_learner_level: Optional[str] = Field(None, description="Suitable level: ประถม, มัธยมต้น, มัธยมปลาย, มหาวิทยาลัย, วัยทำงาน")
    learner_level_reason: Optional[str] = Field(None, description="Explanation for the assigned learner level in Thai")
    content_sufficiency: bool = Field(False, description="Whether the content is deep and actionable enough to generate quality questions")
    sufficiency_reason: Optional[str] = Field(None, description="Reasoning behind the sufficiency decision in Thai")
    should_upload_more_documents: bool = Field(True, description="Flag indicating if the user is recommended to upload more documents")
    recommended_next_action: Optional[str] = Field(None, description="Next actionable step for the user")
    status: str = Field(default="failed", description="'success' or 'failed'")
    message: Optional[str] = Field(None, description="Status message or error in Thai")
    keywords_found: List[str] = Field(default_factory=list, description="Keywords that triggered the classification.")
    analyzed_char_count: int = Field(0, description="Number of text characters processed by the analyzer.")
