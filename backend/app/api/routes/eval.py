from fastapi import APIRouter, Query

from app.models.eval import EvalReport
from eval.harness import run_eval

router = APIRouter()


@router.post("/run", response_model=EvalReport)
async def run_eval_endpoint(
    provider: str = Query(default="groq", description="'groq' or 'gemini'"),
) -> EvalReport:
    """
    Runs the full golden-set eval: ungrounded vs grounded generation,
    both verified against real computed charts. Makes real LLM API calls
    for every chart in the golden set (currently 5) x 2 conditions - not
    something to hit repeatedly in a hot loop, but exactly the endpoint
    the dashboard's headline stat should be wired to.
    """
    return run_eval(provider=provider)
