"""
Pydantic schemas for document analysis results.
Defines the final structured outcome of the Phase 3 analysis process.
"""

from app.schemas.shared.agent_outputs import AnalyzerOutput

class AnalysisResultResponse(AnalyzerOutput):
    """
    Response model for document analysis results.
    Inherits from the shared AnalyzerOutput to avoid redundancy.
    """
    pass
