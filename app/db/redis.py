"""
Redis connection management for QuizSensei.
Provides an async Redis client pool for caching and worker queues.
"""
import logging
from typing import Optional

import redis.asyncio as aioredis

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global connection pool – created once, reused across the app lifetime.
_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Return a shared async Redis client (lazy-initialised).

    Usage as a FastAPI dependency::

        @router.get("/example")
        async def example(cache: aioredis.Redis = Depends(get_redis)):
            await cache.set("key", "value")
    """
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf-8",
        )
        logger.info("Redis connection pool created → %s", settings.REDIS_URL)
    return _redis_pool


async def close_redis() -> None:
    """Gracefully close the Redis connection pool (call on shutdown)."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        _redis_pool = None
        logger.info("Redis connection pool closed.")
