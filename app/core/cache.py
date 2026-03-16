import json
import logging
import functools
from typing import Optional, Callable
from datetime import datetime
from uuid import UUID

import redis
from pydantic import BaseModel as PydanticBaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    """Lazy-init Redis client. Returns None if unavailable or not configured."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    settings = get_settings()
    if not settings.REDIS_URL:
        logger.info("REDIS_URL not set, caching disabled")
        return None
    try:
        client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        _redis_client = client
        logger.info("Redis connected successfully at %s", settings.REDIS_URL)
    except Exception:
        logger.warning("Redis unavailable, caching disabled")
    return _redis_client


class _CacheEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, PydanticBaseModel):
            return obj.model_dump(mode="json")
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


def cached(cache_key: str, ttl_seconds: int = 60):
    """
    Cache-aside decorator for sync FastAPI route handlers.

    Uses a fixed string cache key (no query-param variation).
    Falls through to the real function if Redis is unavailable.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            r = get_redis()
            if r is None:
                logger.info("CACHE SKIP [%s]: Redis not available", cache_key)
                return func(*args, **kwargs)

            try:
                hit = r.get(f"cache:{cache_key}")
                if hit is not None:
                    logger.info("CACHE HIT [%s]: serving from Redis", cache_key)
                    return json.loads(hit)
                logger.info("CACHE MISS [%s]: fetching from DB", cache_key)
            except Exception:
                logger.warning("Redis GET failed for %s, falling through to DB", cache_key)

            result = func(*args, **kwargs)

            try:
                serialized = json.dumps(result, cls=_CacheEncoder)
                r.setex(f"cache:{cache_key}", ttl_seconds, serialized)
                logger.info("CACHE SET [%s]: stored with TTL=%ds", cache_key, ttl_seconds)
            except Exception:
                logger.warning("Redis SET failed for %s, response served uncached", cache_key)

            return result
        return wrapper
    return decorator


def invalidate_cache(*keys: str) -> None:
    """Delete one or more cache keys. No-op if Redis is unavailable."""
    r = get_redis()
    if r is None:
        return
    try:
        r.delete(*(f"cache:{k}" for k in keys))
    except Exception:
        logger.warning("Redis DELETE failed during invalidation")
