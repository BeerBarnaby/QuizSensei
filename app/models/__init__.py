"""
QuizSensei v2 database models.
All models are imported here so Base.metadata.create_all discovers them.
"""
# v2 Models
from app.models.user import User
from app.models.document import Document, DocumentSection
from app.models.source import Source, SourceAnalysis, source_documents
from app.models.quiz import Quiz
from app.models.question import Question, MCQChoice, SourceReference, AuditLog
from app.models.attempt import QuizAttempt, AttemptAnswer

# Legacy v1 models (kept for backwards compatibility during migration)
from app.models.database_models import QuestionRecord, AnswerAttempt

__all__ = [
    # v2
    "User", "Document", "DocumentSection",
    "Source", "SourceAnalysis", "source_documents",
    "Quiz", "Question", "MCQChoice", "SourceReference", "AuditLog",
    "QuizAttempt", "AttemptAnswer",
    # v1 legacy
    "QuestionRecord", "AnswerAttempt",
]
