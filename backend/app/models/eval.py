"""
Schemas for the eval harness. One EvalCase per test chart, comparing its
ungrounded vs grounded hallucination rate. One EvalReport aggregating
across the whole golden set - this is what produces the actual X%->Y%
number for the resume, not an estimate.
"""

from pydantic import BaseModel, computed_field

from app.models.chart import BirthDetails
from app.models.verification import GenerationResult


class EvalCase(BaseModel):
    birth_details: BirthDetails
    ungrounded_result: GenerationResult
    grounded_result: GenerationResult


class EvalReport(BaseModel):
    provider: str
    cases: list[EvalCase]

    @computed_field
    @property
    def avg_ungrounded_hallucination_rate(self) -> float:
        if not self.cases:
            return 0.0
        rates = [c.ungrounded_result.hallucination_rate for c in self.cases]
        return round(sum(rates) / len(rates), 4)

    @computed_field
    @property
    def avg_grounded_hallucination_rate(self) -> float:
        if not self.cases:
            return 0.0
        rates = [c.grounded_result.hallucination_rate for c in self.cases]
        return round(sum(rates) / len(rates), 4)

    @computed_field
    @property
    def relative_reduction(self) -> float:
        """The number the resume bullet actually wants: how much lower
        the grounded rate is, as a fraction of the ungrounded rate.
        Returns 0.0 if the ungrounded rate is already 0 (nothing to
        reduce), rather than dividing by zero."""
        ungrounded = self.avg_ungrounded_hallucination_rate
        if ungrounded == 0.0:
            return 0.0
        grounded = self.avg_grounded_hallucination_rate
        return round((ungrounded - grounded) / ungrounded, 4)
