import asyncio
from datetime import date

from fastapi import APIRouter, Response

from app.models.chart import BirthDetails, ComputedChart, PanchangDay
from app.compute.chart_builder import build_chart
from app.compute.panchang import compute_panchang
from app.db.cache import build_chart_cache_key, get_cached_chart, set_cached_chart

router = APIRouter()


@router.post("/compute", response_model=ComputedChart)
async def compute_chart_endpoint(birth: BirthDetails, response: Response) -> ComputedChart:
    """
    Pure ground-truth computation - no LLM involved. This is what
    generation/ will read from and verification/ will check against.

    Cache-aside via Redis: a cache hit skips recomputation entirely. A
    Redis outage on either read or write degrades this back to always
    computing fresh - it never breaks the response.
    """
    cache_key = build_chart_cache_key(birth)

    cached = await get_cached_chart(cache_key)
    if cached is not None:
        response.headers["X-Cache"] = "HIT"
        return cached

    chart = await asyncio.to_thread(build_chart, birth)
    response.headers["X-Cache"] = "MISS"
    await set_cached_chart(cache_key, chart)
    return chart


@router.get("/panchang/today", response_model=PanchangDay)
async def today_panchang_endpoint() -> PanchangDay:
    """
    Today's panchang alone, no birth details required. Pure compute, no
    LLM - exists specifically so the frontend can show a genuine daily
    fact without needing to run a full chart or narrative generation.
    """
    return compute_panchang(date.today())
