"""
Thin wrappers around the Groq and Gemini SDKs. Kept deliberately minimal -
anything provider-specific stays in this file, so swapping or adding a
provider later doesn't ripple through generator.py or verification/.
"""

from app.core.config import settings


class LLMProviderRateLimitError(Exception):
    """Raised when a provider's SDK reports a rate limit / quota exhaustion.

    Carries enough context for the route layer to turn this into a clean
    503 instead of letting the raw SDK exception escape as an unhandled 500.
    """

    def __init__(self, provider: str, retry_hint: str | None = None):
        self.provider = provider
        self.retry_hint = retry_hint or "try again in a few minutes"
        super().__init__(f"{provider} rate limit hit: {self.retry_hint}")


def _groq_retry_hint(exc: "Exception") -> str | None:
    # Groq's SDK parses the `retry-after` / `retry-after-ms` response headers
    # itself for its own internal retry logic - that same header is the
    # cleanest source of a precise wait time, so read it directly rather
    # than parsing the free-text error message.
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if headers is None:
        return None
    retry_after = headers.get("retry-after")
    if retry_after:
        return f"try again in about {retry_after} seconds"
    return None


def call_groq(system_prompt: str, user_prompt: str) -> str:
    from groq import Groq, RateLimitError

    client = Groq(api_key=settings.groq_api_key)
    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
        )
    except RateLimitError as exc:
        raise LLMProviderRateLimitError("Groq", _groq_retry_hint(exc)) from exc
    return response.choices[0].message.content


def call_gemini(system_prompt: str, user_prompt: str) -> str:
    import google.generativeai as genai
    from google.api_core.exceptions import ResourceExhausted

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        system_instruction=system_prompt,
    )
    try:
        response = model.generate_content(user_prompt)
    except ResourceExhausted as exc:
        raise LLMProviderRateLimitError("Gemini") from exc
    return response.text
