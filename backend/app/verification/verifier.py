"""
The orchestrator: extract claims from narrative, check each one against
the computed chart - rules first (fast, free), LLM judge only for what
rules couldn't resolve. Assembles the final GenerationResult, whose
hallucination_rate property is the number the whole project is built to
produce honestly.
"""

from app.models.chart import ComputedChart
from app.models.verification import GenerationResult, VerifiedClaim, ClaimStatus
from app.verification.claim_extractor import extract_claims
from app.verification.rules import check_rules
from app.verification.llm_judge import judge_claim


def verify_narrative(
    narrative: str,
    chart: ComputedChart,
    model_used: str,
    chart_id: str,
    use_llm_judge: bool = True,
) -> GenerationResult:
    claims = extract_claims(narrative, model_used)
    verified: list[VerifiedClaim] = []

    for claim in claims:
        status, field_path, confidence = check_rules(claim.text, chart)

        if status is None:  # rules couldn't decide
            if use_llm_judge:
                status, field_path, confidence = judge_claim(claim.text, chart)
            else:
                status, field_path, confidence = ClaimStatus.UNVERIFIABLE, None, 0.0

        verified.append(VerifiedClaim(
            claim=claim,
            status=status,
            grounded_field_path=field_path,
            confidence=confidence,
        ))

    return GenerationResult(
        chart_id=chart_id,
        model_used=model_used,
        narrative=narrative,
        claims=verified,
    )
