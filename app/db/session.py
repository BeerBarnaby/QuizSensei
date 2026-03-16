"""
Database session management using SQLAlchemy and asyncpg.
Provides engine and session factory for FastAPI.
"""
from datetime import datetime
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# We use asyncpg for FastAPI's native async routing
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    pool_pre_ping=True
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Declarative base class for models to inherit from
Base = declarative_base()

async def get_db_session() -> AsyncSession:
    """Dependency for injecting DB sessions into FastAPI routes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()
