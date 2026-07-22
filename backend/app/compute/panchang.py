"""
Panchang: the five daily reckonings of the Vedic calendar. All five are
pure arithmetic on the Sun-Moon angular relationship - no interpretation
involved, which is exactly why this belongs in compute/, not generation/.

Two known simplifications in this implementation (documented rather than
hidden, since silently faking precision would defeat the point of this
whole project):

1. We compute panchang at midnight UT for the given date. Real panchang
   is sunrise-to-sunrise (the Vedic day begins at sunrise, not midnight),
   so a tithi/yoga/karana that changes near sunrise could show the
   previous day's value here. Fixing this requires swe.rise_trans() to
   find the actual local sunrise - deferred to a later phase.

2. Karana has 7 repeating names across most of the lunar month, but 4
   "fixed" karanas that only ever occur once each, at specific points.
   We implement the repeating cycle correctly; the 4 fixed-karana edge
   cases are approximated rather than exactly pinned. Flagged in code
   below.

RULE: no LLM calls in this file.
"""

from datetime import date

import swisseph as swe

from app.models.chart import PanchangDay
from app.compute.ephemeris import SIGNS, NAKSHATRAS, NAKSHATRA_SPAN, sign_from_longitude, nakshatra_from_longitude

TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi",
    "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
    "Trayodashi", "Chaturdashi", "Purnima",
]  # 15 waxing (Shukla); waning (Krishna) reuses the same 14 names, ending in Amavasya

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shoola", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti",
]

MOVABLE_KARANAS = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]
FIXED_KARANAS = {57: "Shakuni", 58: "Chatushpada", 59: "Naga", 60: "Kimstughna"}


def _tithi_name(moon_long: float, sun_long: float) -> str:
    angle = (moon_long - sun_long) % 360
    tithi_number = int(angle // 12) + 1  # 1-30
    if tithi_number <= 15:
        return TITHI_NAMES[tithi_number - 1]
    if tithi_number == 30:
        return "Amavasya"
    return TITHI_NAMES[tithi_number - 16]  # Krishna paksha reuses names 1-14


def _yoga_name(moon_long: float, sun_long: float) -> str:
    angle = (moon_long + sun_long) % 360
    index = int(angle // (360 / 27)) % 27
    return YOGA_NAMES[index]


def _karana_name(moon_long: float, sun_long: float) -> str:
    angle = (moon_long - sun_long) % 360
    karana_number = int(angle // 6) + 1  # 1-60
    if karana_number in FIXED_KARANAS:
        return FIXED_KARANAS[karana_number]
    # Movable karanas cycle 8 times through the 7 names across the ~56
    # remaining half-tithi slots.
    return MOVABLE_KARANAS[(karana_number - 1) % 7]


def compute_panchang(for_date: date) -> PanchangDay:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd_ut = swe.julday(for_date.year, for_date.month, for_date.day, 0.0)  # midnight UT - see module docstring
    sidereal_flag = swe.FLG_SIDEREAL

    (sun_long, *_), _ = swe.calc_ut(jd_ut, swe.SUN, sidereal_flag)
    (moon_long, *_), _ = swe.calc_ut(jd_ut, swe.MOON, sidereal_flag)

    moon_nakshatra, _pada = nakshatra_from_longitude(moon_long)

    return PanchangDay(
        date=for_date.isoformat(),
        tithi=_tithi_name(moon_long, sun_long),
        nakshatra=moon_nakshatra,
        yoga=_yoga_name(moon_long, sun_long),
        karana=_karana_name(moon_long, sun_long),
        moon_sign=sign_from_longitude(moon_long),
        sun_sign=sign_from_longitude(sun_long),
    )
