"""
Rule-based verification: regex/keyword matching a claim's text against
ComputedChart fields directly. Fast, free, deterministic - handles the
large majority of claims ("Mars is in the 7th house", "current Mahadasha
is Jupiter"). Returns (None, None, 0.0) when it genuinely can't decide,
which signals the caller to fall back to the LLM judge for that claim.

One rule here is unconditional and runs before anything else: if a claim
uses an unearned subjective intensifier ("rare", "powerful", "unusually"),
it's flagged ungrounded immediately, regardless of whether the underlying
placement is correct - see SUBJECTIVE_INTENSIFIERS below.
"""

import re

from app.models.chart import ComputedChart
from app.models.verification import ClaimStatus

SUBJECTIVE_INTENSIFIERS = [
    "rare", "extremely rare", "unusually", "especially powerful",
    "immensely", "incredibly rare", "once in a lifetime",
]

WORD_TO_NUMBER = {
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
    "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10, "eleventh": 11, "twelfth": 12,
}

HOUSE_PATTERN = re.compile(r"(\d{1,2})(?:st|nd|rd|th)\s+house", re.IGNORECASE)
WORD_HOUSE_PATTERN = re.compile(
    r"(" + "|".join(WORD_TO_NUMBER) + r")\s+house", re.IGNORECASE
)


def _mentioned_house_number(text: str) -> int | None:
    m = HOUSE_PATTERN.search(text)
    if m:
        return int(m.group(1))
    m = WORD_HOUSE_PATTERN.search(text)
    if m:
        return WORD_TO_NUMBER[m.group(1).lower()]
    return None


def check_rules(claim_text: str, chart: ComputedChart) -> tuple[ClaimStatus | None, str | None, float]:
    lowered = claim_text.lower()

    # Unconditional check: unearned subjective language is grounds for
    # flagging regardless of what else the sentence says.
    for phrase in SUBJECTIVE_INTENSIFIERS:
        if phrase in lowered:
            return ClaimStatus.UNGROUNDED, None, 0.95

    matched_paths: list[str] = []
    contradiction_found = False

    # Panchang (today's transit) checked first, and specifically for Sun/
    # Moon sign mentions, so the natal-position loop below can tell the
    # difference between "Sun in Cancer" (today's transit - correct) and
    # a claim about the Sun's *natal* sign (which for this chart is
    # Pisces, a completely different fact). Without this, a claim about
    # today's transiting Sun would get wrongly compared against the
    # birth position and flagged as a false contradiction.
    transit_confirmed_signs: dict[str, str] = {}  # e.g. {"sun": "cancer"}
    panchang = chart.panchang_today
    if panchang is not None:
        panchang_fields = {
            "tithi": panchang.tithi,
            "nakshatra": panchang.nakshatra,
            "yoga": panchang.yoga,
            "karana": panchang.karana,
            "moon_sign": panchang.moon_sign,
            "sun_sign": panchang.sun_sign,
        }
        for field_name, value in panchang_fields.items():
            if value.lower() in lowered:
                matched_paths.append(f"panchang_today.{field_name}")
                if field_name == "sun_sign":
                    transit_confirmed_signs["sun"] = value.lower()
                elif field_name == "moon_sign":
                    transit_confirmed_signs["moon"] = value.lower()

    # Natal positions: check every planet mentioned in the claim, not just
    # the first one, so a sentence bundling several facts ("Moon in Libra
    # and Sun in Cancer, tithi Navami...") gets every fact checked rather
    # than stopping after the first match.
    for idx, position in enumerate(chart.positions):
        planet_lower = position.planet.lower()
        if planet_lower not in lowered:
            continue

        mentioned_house = _mentioned_house_number(lowered)
        if mentioned_house is not None:
            if mentioned_house == position.house:
                matched_paths.append(f"positions[{idx}].house")
            else:
                contradiction_found = True

        if position.sign.lower() in lowered:
            # Skip natal-sign contradiction if this exact sign was already
            # confirmed as today's transit sign for this same planet - see
            # comment above. Otherwise, a mismatch here is a real contradiction.
            already_confirmed_as_transit = (
                planet_lower in transit_confirmed_signs
                and transit_confirmed_signs[planet_lower] == position.sign.lower()
            )
            if not already_confirmed_as_transit:
                matched_paths.append(f"positions[{idx}].sign")

        if position.nakshatra.lower() in lowered:
            matched_paths.append(f"positions[{idx}].nakshatra")

    # Dasha claims, e.g. "current Mahadasha is Jupiter"
    if "dasha" in lowered or "mahadasha" in lowered or "antardasha" in lowered:
        for idx, dasha in enumerate(chart.current_dashas):
            if dasha.lord.lower() in lowered:
                matched_paths.append(f"current_dashas[{idx}].lord")

    if contradiction_found:
        return ClaimStatus.UNGROUNDED, None, 0.9
    if matched_paths:
        # Multiple facts in one claim all check out - join their paths
        # rather than reporting only the first, so the trace is complete.
        return ClaimStatus.GROUNDED, ",".join(matched_paths), 0.95
    return None, None, 0.0  # rules undecided - defer to LLM judge
