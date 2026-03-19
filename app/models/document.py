"""
Document and DocumentSection models for QuizSensei.
Stores uploaded files and their extracted text content.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class Document(Base):
    """
    Represents an uploaded document file.
    Tracks extraction state and stores extracted text directly in the DB.
    """
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, txt, image
    file_size_bytes = Column(BigInteger, nullable=False, default=0)
    storage_path = Column(String(1000), nullable=False)

    # Extraction content
    raw_extracted_text = Column(Text, nullable=True)
    edited_text = Column(Text, nullable=True)
    approved_text = Column(Text, nullable=True)

    # State tracking
    extraction_state = Column(
        String(20), nullable=False, default="uploaded"
    )  # uploaded | extracting | extracted | approved | failed

    # Metadata
    page_count = Column(Integer, nullable=True)
    extraction_metadata = Column(JSONB, nullable=True, default=dict)

    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    extracted_at = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="documents")
    sections = relationship("DocumentSection", back_populates="document", cascade="all, delete-orphan", lazy="selectin")
    sources = relationship("Source", secondary="source_documents", back_populates="documents")


class DocumentSection(Base):
    """
    A section of extracted content within a document.
    Enables granular source attribution in quiz questions.
    """
    __tablename__ = "document_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    section_number = Column(Integer, nullable=False)
    section_title = Column(String(500), nullable=True)
    page_number = Column(Integer, nullable=True)
    content = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False, default=0)

    # Relationships
    document = relationship("Document", back_populates="sections")
