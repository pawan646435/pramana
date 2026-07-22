"""
Redis cache-aside layer for computed charts.

Only ComputedChart is cached here — never a generated narrative or eval
result, since those aren't pure/deterministic given LLM temperature.
Keep that boundary intact when extending this module.

Each function creates its own Redis client per call via
`async with redis.from_url(...) as client:` rather than a module-level
singleton. A singleton was tried first and caused a real bug - "Event
loop is closed" on the second request in a session, because the client
got bound to whichever event loop existed at construction time. Any new
Redis usage must follow this same per-call-client pattern.

Every function fails soft: a Redis outage degrades performance (no
caching) but must never break the actual API response.
"""

import logging

import redis.asyncio as redis

from app.core.config import settings
from app.models.chart import BirthDetails, ComputedChart

logger = logging.getLogger(__name__)

CHART_CACHE_TTL_SECONDS = 60 * 60 * 12  # half a day - well within one panchang_today validity window


def build_chart_cache_key(birth: BirthDetails) -> str:
    """
    Deterministic key. Includes today's date so entries naturally expire
    (in effect, via key change) when panchang_today would go stale.
    """
    from datetime import date

    return (
        f"chart:{birth.date}:{birth.time}:{birth.latitude}:{birth.longitude}:"
        f"{birth.timezone_offset_hours}:{date.today().isoformat()}"
    )


async def get_cached_chart(key: str) -> ComputedChart | None:
    try:
        async with redis.from_url(settings.redis_url) as client:
            raw = await client.get(key)
    except Exception:
        logger.warning("Redis read failed for chart cache key=%s", key, exc_info=True)
        return None

    if raw is None:
        return None

    try:
        return ComputedChart.model_validate_json(raw)
    except Exception:
        logger.warning("Cached chart failed to deserialize for key=%s", key, exc_info=True)
        return None


async def set_cached_chart(key: str, chart: ComputedChart) -> None:
    try:
        async with redis.from_url(settings.redis_url) as client:
            await client.set(key, chart.model_dump_json(), ex=CHART_CACHE_TTL_SECONDS)
    except Exception:
        logger.warning("Redis write failed for chart cache key=%s", key, exc_info=True)
