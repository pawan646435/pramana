"""
Short-TTL Redis cache for the read-heavy /api/history endpoints.

Kept separate from app/db/cache.py because the thing being cached is
different in kind: app/db/cache.py caches a deterministic ComputedChart
indefinitely (well, until the day rolls over); this caches a snapshot of
"recent rows in Postgres", which changes as new evals/generations come
in - hence the short TTL instead of a content-derived key.

Same per-call-client pattern as app/db/cache.py, same fail-soft
contract: a cache failure here just means the route falls back to
querying Postgres directly, never a broken response.
"""

import json
import logging

import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)

HISTORY_CACHE_TTL_SECONDS = 45


async def get_cached_json(key: str) -> object | None:
    try:
        async with redis.from_url(settings.redis_url) as client:
            raw = await client.get(key)
    except Exception:
        logger.warning("Redis read failed for history cache key=%s", key, exc_info=True)
        return None

    if raw is None:
        return None

    try:
        return json.loads(raw)
    except Exception:
        logger.warning("Cached history payload failed to deserialize for key=%s", key, exc_info=True)
        return None


async def set_cached_json(key: str, value: object) -> None:
    try:
        async with redis.from_url(settings.redis_url) as client:
            await client.set(key, json.dumps(value), ex=HISTORY_CACHE_TTL_SECONDS)
    except Exception:
        logger.warning("Redis write failed for history cache key=%s", key, exc_info=True)
