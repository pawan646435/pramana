import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.persistence import persist_generation_log
from app.db.session import get_db_session
from app.models.chart import BirthDetails
from app.models.verification import GenerationResult
from app.compute.chart_builder import build_chart
from app.generation.clients import LLMProviderRateLimitError
from app.generation.generator import generate_narrative
from app.verification.verifier import verify_narrative

router = APIRouter()


@router.post("/narrative", response_model=GenerationResult)
async def generate_and_verify(
    birth: BirthDetails,
    provider: str = Query(default="groq", description="'groq' or 'gemini'"),
    session: AsyncSession = Depends(get_db_session),
) -> GenerationResult:
    chart = await asyncio.to_thread(build_chart, birth)
    try:
        narrative, model_used = await asyncio.to_thread(generate_narrative, chart, provider)
    except LLMProviderRateLimitError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"The AI provider ({exc.provider}) has hit its rate limit for "
                "today. This usually resolves within a few minutes - please "
                "try again shortly."
            ),
        ) from exc
    result = await asyncio.to_thread(
        verify_narrative,
        narrative=narrative,
        chart=chart,
        model_used=model_used,
        chart_id=str(uuid.uuid4()),
    )
    await persist_generation_log(session, birth=birth, provider=provider, result=result)
    return result
