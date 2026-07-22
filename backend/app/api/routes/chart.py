from fastapi import APIRouter

from app.models.chart import BirthDetails, ComputedChart
from app.compute.chart_builder import build_chart

router = APIRouter()


@router.post("/compute", response_model=ComputedChart)
async def compute_chart_endpoint(birth: BirthDetails) -> ComputedChart:
    """
    Pure ground-truth computation - no LLM involved. This is what
    generation/ will read from and verification/ will check against.
    """
    return build_chart(birth)
