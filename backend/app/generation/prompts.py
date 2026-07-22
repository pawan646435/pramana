"""
Prompt construction for the narrative layer.

The entire grounding strategy lives in this prompt: the model is handed
the computed chart as JSON and explicitly forbidden from adding anything
not present in it. Verification later checks whether it actually
complied - this prompt is the first line of defense, not the only one.
"""

from app.models.chart import ComputedChart

SYSTEM_PROMPT = """You are an astrological narrator. You will be given a JSON object
containing a fully computed Vedic birth chart - planetary positions, current dasha
periods, and today's panchang. All of this data is already correct and complete.

Your only job is to narrate it in natural, warm language. Strict rules:

1. Only state facts that are explicitly present in the JSON. Do not invent placements,
   dates, or dasha periods that aren't in the data.
2. Do not use subjective intensifiers with no basis in the data - words like "rare",
   "powerful", "unusually", "extremely rare alignment" are not present in the JSON and
   must not appear in your narration.
3. You may offer standard, well-known interpretive meaning for a placement (e.g. "Mars
   in the 7th house often relates to partnerships") as long as the placement itself
   (planet, house, sign, nakshatra) is drawn directly from the JSON.
4. Do not mention planets, houses, or periods that are absent from the JSON.
5. Keep the narration to 4-6 sentences.
"""


def build_narration_prompt(chart: ComputedChart) -> str:
    chart_json = chart.model_dump_json(indent=2)
    return f"""Here is the computed chart:

{chart_json}

Write a short natural-language narration of this chart, following the system rules exactly."""
