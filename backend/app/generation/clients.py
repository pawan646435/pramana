"""
Thin wrappers around the Groq and Gemini SDKs. Kept deliberately minimal -
anything provider-specific stays in this file, so swapping or adding a
provider later doesn't ripple through generator.py or verification/.
"""

from app.core.config import settings


def call_groq(system_prompt: str, user_prompt: str) -> str:
    from groq import Groq

    client = Groq(api_key=settings.groq_api_key)
    response = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content


def call_gemini(system_prompt: str, user_prompt: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(
        model_name=settings.gemini_model,
        system_instruction=system_prompt,
    )
    response = model.generate_content(user_prompt)
    return response.text
