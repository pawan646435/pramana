"""
Prompt construction for the narrative layer.

The entire grounding strategy lives in this prompt: the model is handed
the computed chart as JSON and explicitly forbidden from adding anything
not present in it. Verification later checks whether it actually
complied - this prompt is the first line of defense, not the only one.
"""

from app.models.chart import BirthDetails, ComputedChart

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

Write 10-14 sentences, organized to cover:
1. The placements of all seven grahas (Sun, Moon, Mercury, Venus, Mars, Jupiter,
   Saturn), each with its sign, house, and nakshatra.
2. The current Mahadasha and Antardasha.
3. Today's panchang details: tithi, nakshatra, and yoga.
4. Brief, standard interpretive context for 2-3 of the most notable placements, per
   rule 3 above.
"""


def build_narration_prompt(chart: ComputedChart) -> str:
    chart_json = chart.model_dump_json(indent=2)
    return f"""Here is the computed chart:

{chart_json}

Write a natural-language narration of this chart, following the system rules exactly."""


UNGROUNDED_SYSTEM_PROMPT = """You are a Vedic astrologer. A person has given you their birth
date, time, and place. Write a natural-language astrological reading for them.

Write 10-14 sentences, organized to cover:
1. The placements of all seven grahas (Sun, Moon, Mercury, Venus, Mars, Jupiter,
   Saturn), each with its sign, house, and nakshatra.
2. Their current Mahadasha and Antardasha.
3. Today's panchang details: tithi, nakshatra, and yoga.
4. Brief, standard interpretive context for 2-3 of the most notable placements.
"""


def build_ungrounded_prompt(birth: BirthDetails) -> str:
    """
    Deliberately gives the model NO computed chart data - only raw birth
    details, the way a naive astrology app (or a person asking ChatGPT
    directly) would. This is the eval baseline: whatever specific
    placements the model states here, it invented from parametric
    "knowledge" rather than real computation, since it has no way to
    actually calculate them from birth details alone.
    """
    return f"""Birth date: {birth.date}
Birth time: {birth.time}
Birth location: latitude {birth.latitude}, longitude {birth.longitude}

Write the astrological reading now, following the system rules exactly - specific
planetary placements (sign, house, nakshatra) for all seven grahas, the current
dasha period, and today's panchang."""
