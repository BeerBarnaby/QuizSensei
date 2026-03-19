"""
QuizAttempt and AttemptAnswer models for QuizSensei.
Tracks student quiz-taking sessions and individual answers with diagnostic feedback.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class QuizAttempt(Base):
    """
    Represents a student's attempt at taking a quiz.
    Agent 4 (Grader) provides diagnostic feedback on completion.
    """
    __tablename__ = "quiz_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    # State
    state = Column(String(20), nullable=False, default="in_progress")  # in_progress | graded
    score = Column(Integer, nullable=True)
    total_questions = Column(Integer, nullable=False, default=0)

    # Agent 4 overall diagnostic (set on completion)
    diagnostic_summary_th = Column(Text, nullable=True)

    # Timestamps
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    quiz = relationship("Quiz", back_populates="attempts")
    answers = relationship("AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan", lazy="selectin")


class AttemptAnswer(Base):
    """
    A single answer submitted by a student during a quiz attempt.
    Stores Agent 4's per-question diagnostic feedback.
    """
    __tablename__ = "attempt_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quiz_attempt_id = Column(UUID(as_uuid=True), ForeignKey("quiz_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(UUID(as_uuid=True), ForeignKey("v2_questions.id"), nullable=False, index=True)

    selected_key = Column(String(5), nullable=False)  # A | B | C | D
    is_correct = Column(Boolean, nullable=False)
    diagnostic_feedback_th = Column(Text, nullable=True)  # Agent 4 per-question feedback

    answered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    attempt = relationship("QuizAttempt", back_populates="answers")
