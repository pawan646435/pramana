"""
Writes pydantic results (EvalReport, GenerationResult) into Postgres as
ORM rows. Called from the API route layer after a result already exists
and is about to be returned - persistence here is purely additive and
must never be the reason a request fails.

Every function fails soft: it logs and returns on any DB error rather
than raising, so a Postgres outage degrades to "this run wasn't
recorded" instead of breaking the actual API response.
"""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EvalCase as EvalCaseRow
from app.db.models import EvalRun, GenerationLog
from app.models.chart import BirthDetails
from app.models.eval import EvalReport
from app.models.verification import ClaimStatus, GenerationResult

logger = logging.getLogger(__name__)


async def persist_eval_report(session: AsyncSession, report: EvalReport) -> None:
    try:
        run = EvalRun(
            provider=report.provider,
            avg_ungrounded_hallucination_rate=report.avg_ungrounded_hallucination_rate,
            avg_grounded_hallucination_rate=report.avg_grounded_hallucination_rate,
            relative_reduction=report.relative_reduction,
            num_cases=len(report.cases),
        )
        session.add(run)

        for case in report.cases:
            birth: BirthDetails = case.birth_details
            session.add(
                EvalCaseRow(
                    eval_run=run,
                    birth_date=birth.date,
                    birth_time=birth.time,
                    latitude=birth.latitude,
                    longitude=birth.longitude,
                    timezone_offset_hours=birth.timezone_offset_hours,
                    ungrounded_hallucination_rate=case.ungrounded_result.hallucination_rate,
                    grounded_hallucination_rate=case.grounded_result.hallucination_rate,
                    ungrounded_narrative=case.ungrounded_result.narrative,
                    grounded_narrative=case.grounded_result.narrative,
                )
            )

        await session.commit()
    except Exception:
        logger.warning("Failed to persist eval report to Postgres", exc_info=True)
        await session.rollback()


async def persist_generation_log(
    session: AsyncSession,
    birth: BirthDetails,
    provider: str,
    result: GenerationResult,
) -> None:
    try:
        num_grounded = sum(1 for c in result.claims if c.status == ClaimStatus.GROUNDED)
        num_ungrounded = sum(1 for c in result.claims if c.status == ClaimStatus.UNGROUNDED)
        num_unverifiable = sum(1 for c in result.claims if c.status == ClaimStatus.UNVERIFIABLE)

        claims_detail = [
            {
                "text": c.claim.text,
                "source_model": c.claim.source_model,
                "status": c.status.value,
                "grounded_field_path": c.grounded_field_path,
                "confidence": c.confidence,
            }
            for c in result.claims
        ]

        session.add(
            GenerationLog(
                birth_date=birth.date,
                birth_time=birth.time,
                latitude=birth.latitude,
                longitude=birth.longitude,
                timezone_offset_hours=birth.timezone_offset_hours,
                provider=provider,
                model_used=result.model_used,
                narrative=result.narrative,
                hallucination_rate=result.hallucination_rate,
                num_claims=len(result.claims),
                num_grounded_claims=num_grounded,
                num_ungrounded_claims=num_ungrounded,
                num_unverifiable_claims=num_unverifiable,
                claims_detail=claims_detail,
            )
        )
        await session.commit()
    except Exception:
        logger.warning("Failed to persist generation log to Postgres", exc_info=True)
        await session.rollback()
