"""Redis client — with graceful fallback if Redis is unavailable."""
import json
from typing import Any, Optional
import structlog

logger = structlog.get_logger(__name__)

_redis_client = None

async def get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            import redis.asyncio as aioredis
            from core.config import settings
            _redis_client = aioredis.from_url(
                settings.REDIS_URL, encoding="utf-8", decode_responses=True, max_connections=10
            )
            await _redis_client.ping()
        except Exception as e:
            logger.warning("redis_unavailable", error=str(e))
            _redis_client = None
    return _redis_client

async def cache_set(key: str, value: Any, ttl: int = 3600) -> bool:
    try:
        r = await get_redis()
        if r is None: return False
        await r.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception as e:
        logger.warning("cache_set_failed", key=key, error=str(e))
        return False

async def cache_get(key: str) -> Optional[Any]:
    try:
        r = await get_redis()
        if r is None: return None
        value = await r.get(key)
        return json.loads(value) if value else None
    except Exception as e:
        logger.warning("cache_get_failed", key=key, error=str(e))
        return None

async def cache_delete(key: str) -> bool:
    try:
        r = await get_redis()
        if r is None: return False
        await r.delete(key)
        return True
    except Exception as e:
        return False

async def cache_delete_pattern(pattern: str) -> int:
    try:
        r = await get_redis()
        if r is None: return 0
        keys = await r.keys(pattern)
        if keys: return await r.delete(*keys)
        return 0
    except Exception as e:
        return 0
