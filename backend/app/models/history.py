"""
Response schemas for the /api/history endpoints. These are new,
additive models for reading persisted rows back out - they don't
replace or alias any existing pydantic model (ComputedChart,
GenerationResult, EvalReport, ...), which stay exactly as they are.
"""

from datetime import datetime

from pydantic import BaseModel


class EvalRunSummary(BaseModel):
    id: str
    provider: str
    avg_ungrounded_hallucination_rate: float
    avg_grounded_hallucination_rate: float
    relative_reduction: float
    num_cases: int
    created_at: datetime


class EvalCaseDetail(BaseModel):
    id: str
    birth_date: str
    birth_time: str
    latitude: float
    longitude: float
    timezone_offset_hours: float
    ungrounded_hallucination_rate: float
    grounded_hallucination_rate: float
    ungrounded_narrative: str
    grounded_narrative: str
    created_at: datetime


class EvalRunDetail(EvalRunSummary):
    cases: list[EvalCaseDetail]


class GenerationLogSummary(BaseModel):
    id: str
    birth_date: str
    birth_time: str
    latitude: float
    longitude: float
    timezone_offset_hours: float
    provider: str
    model_used: str
    narrative: str
    hallucination_rate: float
    num_claims: int
    num_grounded_claims: int
    num_ungrounded_claims: int
    num_unverifiable_claims: int
    claims_detail: list[dict]
    created_at: datetime
