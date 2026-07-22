from datetime import date

from fastapi import APIRouter

from app.models.chart import BirthDetails, ComputedChart, PanchangDay
from app.compute.chart_builder import build_chart
from app.compute.panchang import compute_panchang

router = APIRouter()


@router.post("/compute", response_model=ComputedChart)
async def compute_chart_endpoint(birth: BirthDetails) -> ComputedChart:
    """
    Pure ground-truth computation - no LLM involved. This is what
    generation/ will read from and verification/ will check against.
    """
    return build_chart(birth)


@router.get("/panchang/today", response_model=PanchangDay)
async def today_panchang_endpoint() -> PanchangDay:
    """
    Today's panchang alone, no birth details required. Pure compute, no
    LLM - exists specifically so the frontend can show a genuine daily
    fact without needing to run a full chart or narrative generation.
    """
    return compute_panchang(date.today())
