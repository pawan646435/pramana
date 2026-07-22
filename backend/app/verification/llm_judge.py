"""
LLM-as-judge: only called for claims check_rules() couldn't resolve.
Given the full computed chart and one claim, asks the model to decide
whether the claim is grounded, ungrounded, or genuinely unverifiable
(interpretive language with nothing to check against).

This is deliberately the expensive path, used sparingly - most claims
should never reach this function if the rule engine and prompt are doing
their jobs. If eval numbers later show this function firing on the
majority of claims, that's a signal to expand rules.py, not to lean
harder on this fallback.
"""

import json

from app.models.chart import ComputedChart
from app.models.verification import ClaimStatus

JUDGE_SYSTEM_PROMPT = """You are a strict fact-checker. You will be given a computed
astrological chart as JSON, and one claim made about that chart. Decide:

- "grounded" - the claim is directly and specifically supported by a field in the JSON
- "ungrounded" - the claim states something not present in, or contradicted by, the JSON
- "unverifiable" - the claim is interpretive/subjective phrasing with nothing in the
  JSON that could confirm or deny it (e.g. general encouragement, vague sentiment)

Respond with ONLY a JSON object, no other text:
{"status": "grounded" | "ungrounded" | "unverifiable", "field_path": "<dot path or null>", "confidence": <0.0-1.0>}
"""


def judge_claim(claim_text: str, chart: ComputedChart) -> tuple[ClaimStatus, str | None, float]:
    from app.generation.clients import call_groq

    user_prompt = f"""Chart JSON:
{chart.model_dump_json(indent=2)}

Claim to check: "{claim_text}"
"""
    raw = call_groq(JUDGE_SYSTEM_PROMPT, user_prompt)

    try:
        parsed = json.loads(raw)
        status = ClaimStatus(parsed["status"])
        return status, parsed.get("field_path"), float(parsed.get("confidence", 0.5))
    except (json.JSONDecodeError, KeyError, ValueError):
        # If the judge itself doesn't return clean JSON, don't silently
        # assume grounded - treat it as unverifiable and surface it.
        return ClaimStatus.UNVERIFIABLE, None, 0.0
