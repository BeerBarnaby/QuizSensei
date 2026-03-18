"""
User model for QuizSensei.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    """Represents a platform user (teacher or student)."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name = Column(String(200), nullable=False)
    email = Column(String(320), unique=True, nullable=False, index=True)
    role = Column(String(20), nullable=False, default="teacher")  # teacher | student
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    documents = relationship("Document", back_populates="user", lazy="selectin")
    sources = relationship("Source", back_populates="user", lazy="selectin")
