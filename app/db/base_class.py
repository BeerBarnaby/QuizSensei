"""
Declarative base class for all SQLAlchemy ORM models.
Separated from session.py to prevent circular imports.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models.
    
    Models should define their own __tablename__ explicitly.
    """
    pass
