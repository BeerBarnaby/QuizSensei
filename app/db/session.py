"""
Database session management using SQLAlchemy and asyncpg.
Provides engine and session factory for FastAPI.
"""
from datetime import datetime
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import get_settings
from app.db.base_class import Base

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

# The declarative Base is imported from base_class to prevent circular dependencies

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for injecting DB sessions into FastAPI routes."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()
