"""
Orchestrates narrative generation: build the prompt from a ComputedChart,
call the chosen provider, return the raw text. Deliberately returns raw,
unverified narrative - verification/ is a separate step, on purpose, so
"generated" and "checked" never get conflated into one function.
"""

from app.models.chart import BirthDetails, ComputedChart
from app.generation.prompts import (
    SYSTEM_PROMPT, build_narration_prompt,
    UNGROUNDED_SYSTEM_PROMPT, build_ungrounded_prompt,
)
from app.generation.clients import call_groq, call_gemini

PROVIDERS = {
    "groq": call_groq,
    "gemini": call_gemini,
}


def generate_narrative(chart: ComputedChart, provider: str = "groq") -> tuple[str, str]:
    """Returns (narrative_text, model_identifier_used)."""
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider '{provider}'. Choose from: {list(PROVIDERS)}")

    user_prompt = build_narration_prompt(chart)
    narrative = PROVIDERS[provider](SYSTEM_PROMPT, user_prompt)

    from app.core.config import settings
    model_identifier = settings.groq_model if provider == "groq" else settings.gemini_model
    return narrative, f"{provider}:{model_identifier}"


def generate_ungrounded_narrative(birth: BirthDetails, provider: str = "groq") -> tuple[str, str]:
    """
    The eval baseline: same provider, same birth details, but no computed
    chart handed to the model - it must state specific placements from
    parametric "knowledge" rather than real calculation. Used only by the
    eval harness to measure what hallucination rate looks like without
    grounding, for comparison against generate_narrative()'s rate.
    """
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider '{provider}'. Choose from: {list(PROVIDERS)}")

    user_prompt = build_ungrounded_prompt(birth)
    narrative = PROVIDERS[provider](UNGROUNDED_SYSTEM_PROMPT, user_prompt)

    from app.core.config import settings
    model_identifier = settings.groq_model if provider == "groq" else settings.gemini_model
    return narrative, f"{provider}:{model_identifier}"
