"""
Orchestrates narrative generation: build the prompt from a ComputedChart,
call the chosen provider, return the raw text. Deliberately returns raw,
unverified narrative - verification/ is a separate step, on purpose, so
"generated" and "checked" never get conflated into one function.
"""

from app.models.chart import ComputedChart
from app.generation.prompts import SYSTEM_PROMPT, build_narration_prompt
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
