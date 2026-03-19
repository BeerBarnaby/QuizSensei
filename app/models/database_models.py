"""
SQLAlchemy database models for storing questions, answer attempts, and analytics data.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base

class QuestionRecord(Base):
    """
    SQLAlchemy Model for storing generated questions.
    Links the generated JSON drafts to relational rows for analytics.
    """
    __tablename__ = "questions"

    id = Column(String(50), primary_key=True, index=True)
    document_id = Column(String(50), nullable=False, index=True)
    topic = Column(String(100), nullable=False)
    subtopic = Column(String(100), nullable=False)
    indicator_id = Column(String(50), nullable=True)
    difficulty = Column(String(20), nullable=False)
    
    # Store the entire complex Question Draft schema as JSON payload
    payload = Column(JSON, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to user answer attempts (for calculating p-value)
    attempts = relationship("AnswerAttempt", back_populates="question")


class AnswerAttempt(Base):
    """
    SQLAlchemy Model for storing a user's attempt at answering a question.
    Used to calculate the Difficulty Index (p-value).
    """
    __tablename__ = "answer_attempts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(String(50), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(100), nullable=True, index=True) # Optional for MVP anonymous users
    
    selected_choice_key = Column(String(10), nullable=False)
    is_correct = Column(Integer, nullable=False) # 1 for True, 0 for False (for easier sum math)
    
    submitted_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to the question
    question = relationship("QuestionRecord", back_populates="attempts")
