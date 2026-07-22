"""
Schemas for the generation and verification layers.

A "claim" is one atomic, checkable statement extracted from LLM output.
Splitting narrative text into claims is what makes hallucination rate a
measurable number instead of a vibe.
"""

from enum import Enum
from pydantic import BaseModel, computed_field


class ClaimStatus(str, Enum):
    GROUNDED = "grounded"       # traced to a specific field in ComputedChart
    UNGROUNDED = "ungrounded"   # no traceable source — flagged
    UNVERIFIABLE = "unverifiable"  # subjective/interpretive, not fact-checkable by design


class ExtractedClaim(BaseModel):
    text: str
    source_model: str  # e.g. "groq-llama-3.3-70b"


class VerifiedClaim(BaseModel):
    claim: ExtractedClaim
    status: ClaimStatus
    grounded_field_path: str | None = None  # e.g. "positions[2].house"
    confidence: float


class GenerationResult(BaseModel):
    chart_id: str
    model_used: str
    narrative: str
    claims: list[VerifiedClaim]

    @computed_field
    @property
    def hallucination_rate(self) -> float:
        if not self.claims:
            return 0.0
        ungrounded = sum(1 for c in self.claims if c.status == ClaimStatus.UNGROUNDED)
        return round(ungrounded / len(self.claims), 4)
