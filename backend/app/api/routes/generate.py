import uuid

from fastapi import APIRouter, Query

from app.models.chart import BirthDetails
from app.models.verification import GenerationResult
from app.compute.chart_builder import build_chart
from app.generation.generator import generate_narrative
from app.verification.verifier import verify_narrative

router = APIRouter()


@router.post("/narrative", response_model=GenerationResult)
async def generate_and_verify(
    birth: BirthDetails,
    provider: str = Query(default="groq", description="'groq' or 'gemini'"),
) -> GenerationResult:
    chart = build_chart(birth)
    narrative, model_used = generate_narrative(chart, provider=provider)
    return verify_narrative(
        narrative=narrative,
        chart=chart,
        model_used=model_used,
        chart_id=str(uuid.uuid4()),
    )
