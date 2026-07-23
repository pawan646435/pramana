import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.persistence import persist_eval_report
from app.db.session import get_db_session
from app.generation.clients import LLMProviderRateLimitError
from app.models.eval import EvalReport
from eval.harness import run_eval

router = APIRouter()


@router.post("/run", response_model=EvalReport)
async def run_eval_endpoint(
    provider: str = Query(default="groq", description="'groq' or 'gemini'"),
    session: AsyncSession = Depends(get_db_session),
) -> EvalReport:
    """
    Runs the full golden-set eval: ungrounded vs grounded generation,
    both verified against real computed charts. Makes real LLM API calls
    for every chart in the golden set (currently 5) x 2 conditions - not
    something to hit repeatedly in a hot loop, but exactly the endpoint
    the dashboard's headline stat should be wired to.

    The run and its per-chart cases are persisted to Postgres for
    history, additively - a persistence failure is logged and never
    changes what's returned here.
    """
    try:
        report = await asyncio.to_thread(run_eval, provider)
    except LLMProviderRateLimitError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"The AI provider ({exc.provider}) has hit its rate limit for "
                "today. This usually resolves within a few minutes - please "
                "try again shortly."
            ),
        ) from exc
    await persist_eval_report(session, report)
    return report
