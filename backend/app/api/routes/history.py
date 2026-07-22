"""
Read-only history endpoints over persisted eval runs and generation
logs. Each is wrapped with a short-TTL Redis cache (app/db/history_cache)
- a cache-read/write failure falls back to querying Postgres directly,
never breaks the response.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.history_cache import get_cached_json, set_cached_json
from app.db.models import EvalCase, EvalRun, GenerationLog
from app.db.session import get_db_session
from app.models.history import EvalCaseDetail, EvalRunDetail, EvalRunSummary, GenerationLogSummary

router = APIRouter()


def _eval_run_to_summary(row: EvalRun) -> EvalRunSummary:
    return EvalRunSummary(
        id=str(row.id),
        provider=row.provider,
        avg_ungrounded_hallucination_rate=row.avg_ungrounded_hallucination_rate,
        avg_grounded_hallucination_rate=row.avg_grounded_hallucination_rate,
        relative_reduction=row.relative_reduction,
        num_cases=row.num_cases,
        created_at=row.created_at,
    )


def _eval_case_to_detail(row: EvalCase) -> EvalCaseDetail:
    return EvalCaseDetail(
        id=str(row.id),
        birth_date=row.birth_date,
        birth_time=row.birth_time,
        latitude=row.latitude,
        longitude=row.longitude,
        timezone_offset_hours=row.timezone_offset_hours,
        ungrounded_hallucination_rate=row.ungrounded_hallucination_rate,
        grounded_hallucination_rate=row.grounded_hallucination_rate,
        ungrounded_narrative=row.ungrounded_narrative,
        grounded_narrative=row.grounded_narrative,
        created_at=row.created_at,
    )


def _generation_log_to_summary(row: GenerationLog) -> GenerationLogSummary:
    return GenerationLogSummary(
        id=str(row.id),
        birth_date=row.birth_date,
        birth_time=row.birth_time,
        latitude=row.latitude,
        longitude=row.longitude,
        timezone_offset_hours=row.timezone_offset_hours,
        provider=row.provider,
        model_used=row.model_used,
        narrative=row.narrative,
        hallucination_rate=row.hallucination_rate,
        num_claims=row.num_claims,
        num_grounded_claims=row.num_grounded_claims,
        num_ungrounded_claims=row.num_ungrounded_claims,
        num_unverifiable_claims=row.num_unverifiable_claims,
        claims_detail=row.claims_detail,
        created_at=row.created_at,
    )


@router.get("/eval-runs", response_model=list[EvalRunSummary])
async def list_eval_runs(
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> list[EvalRunSummary]:
    cache_key = f"history:eval-runs:{limit}"
    cached = await get_cached_json(cache_key)
    if cached is not None:
        return [EvalRunSummary.model_validate(item) for item in cached]

    result = await session.execute(
        select(EvalRun).order_by(EvalRun.created_at.desc()).limit(limit)
    )
    summaries = [_eval_run_to_summary(row) for row in result.scalars().all()]

    await set_cached_json(cache_key, [s.model_dump(mode="json") for s in summaries])
    return summaries


@router.get("/eval-runs/{eval_run_id}", response_model=EvalRunDetail)
async def get_eval_run(
    eval_run_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> EvalRunDetail:
    try:
        run_uuid = uuid.UUID(eval_run_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Eval run not found")

    cache_key = f"history:eval-run:{eval_run_id}"
    cached = await get_cached_json(cache_key)
    if cached is not None:
        return EvalRunDetail.model_validate(cached)

    result = await session.execute(
        select(EvalRun)
        .where(EvalRun.id == run_uuid)
        .options(selectinload(EvalRun.cases))
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Eval run not found")

    detail = EvalRunDetail(
        **_eval_run_to_summary(row).model_dump(),
        cases=[_eval_case_to_detail(c) for c in row.cases],
    )

    await set_cached_json(cache_key, detail.model_dump(mode="json"))
    return detail


@router.get("/generations", response_model=list[GenerationLogSummary])
async def list_generations(
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> list[GenerationLogSummary]:
    cache_key = f"history:generations:{limit}"
    cached = await get_cached_json(cache_key)
    if cached is not None:
        return [GenerationLogSummary.model_validate(item) for item in cached]

    result = await session.execute(
        select(GenerationLog).order_by(GenerationLog.created_at.desc()).limit(limit)
    )
    summaries = [_generation_log_to_summary(row) for row in result.scalars().all()]

    await set_cached_json(cache_key, [s.model_dump(mode="json") for s in summaries])
    return summaries
