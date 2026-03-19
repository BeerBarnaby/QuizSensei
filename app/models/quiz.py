"""
Quiz model for QuizSensei.
Represents a generated quiz attached to a Source.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class Quiz(Base):
    """
    A quiz generated from a Source by Agent 2 and validated by Agent 3.
    """
    __tablename__ = "quizzes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    # Generation parameters
    learner_level = Column(String(30), nullable=False)  # primary | middle_school | ...
    difficulty = Column(String(20), nullable=False)  # easy | medium | hard
    num_questions = Column(Integer, nullable=False, default=5)

    # State
    state = Column(
        String(20), nullable=False, default="generating"
    )  # generating | auditing | ready | failed
    generation_attempts = Column(Integer, nullable=False, default=0)

    # Timestamps
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    source = relationship("Source", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan", lazy="selectin")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")
