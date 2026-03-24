"""
QuizSensei v2 database models.
All models are imported here so Base.metadata.create_all discovers them.
"""
# v2 Models
from app.models.document import Document, DocumentSection
from app.models.source import Source, SourceAnalysis, source_documents
from app.models.quiz import Quiz
from app.models.question import Question, MCQChoice, SourceReference, AuditLog

__all__ = [
    "Document", "DocumentSection",
    "Source", "SourceAnalysis", "source_documents",
    "Quiz", "Question", "MCQChoice", "SourceReference", "AuditLog",
]
