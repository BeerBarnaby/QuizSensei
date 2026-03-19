"""
Source and SourceAnalysis models for QuizSensei.
A Source groups one or more Documents for combined analysis and quiz generation.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


# Many-to-many association table: Source <-> Document
source_documents = Table(
    "source_documents",
    Base.metadata,
    Column("source_id", UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True),
    Column("document_id", UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
)


class Source(Base):
    """
    A logical grouping of documents for quiz generation.
    Represents a 'notebook' or 'source collection' in the UI.
    """
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    name = Column(String(500), nullable=False)
    state = Column(
        String(30), nullable=False, default="created"
    )  # created | analyzing | ready | insufficient | generating | quiz_ready
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="sources")
    documents = relationship("Document", secondary=source_documents, back_populates="sources", lazy="selectin")
    analysis = relationship("SourceAnalysis", back_populates="source", uselist=False, cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="source", cascade="all, delete-orphan", lazy="selectin")


class SourceAnalysis(Base):
    """
    AI-generated analysis of a Source's combined document content.
    Produced by Agent 1 (Analyzer). Determines sufficiency and suggests learner level.
    """
    __tablename__ = "source_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Thai-language analysis
    summary_th = Column(Text, nullable=True)
    topics = Column(JSONB, nullable=True, default=list)  # ["topic1", "topic2"]
    subtopics = Column(JSONB, nullable=True, default=list)
    key_concepts = Column(JSONB, nullable=True, default=list)
    indicators = Column(JSONB, nullable=True, default=list)  # [{"id": "IND-01", "text": "..."}]

    # Gatekeeper
    is_sufficient = Column(Boolean, nullable=False, default=False)
    insufficiency_reason_th = Column(Text, nullable=True)
    suggested_learner_level = Column(String(30), nullable=True)
    estimated_question_capacity = Column(Integer, nullable=True)

    # Metadata
    analyzed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    source = relationship("Source", back_populates="analysis")
