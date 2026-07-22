"""
Deterministic astronomical computation.

RULE: nothing in this module or its neighbors (dasha.py, panchang.py) may
import from app.generation or app.verification, and no function here may
call an LLM. This is the ground truth layer.

Concepts, briefly:

- Vedic astrology uses the SIDEREAL zodiac (fixed stars), not the
  TROPICAL zodiac (seasons) that Western astrology uses. The gap between
  them today is ~24 degrees, called the ayanamsa. We use the Lahiri
  ayanamsa, the standard for Vedic charts. swe.set_sid_mode() tells
  Swiss Ephemeris to subtract it automatically when we ask for sidereal
  positions.

- Swiss Ephemeris gives raw longitude (0-360 degrees) per planet. Sign,
  house, and nakshatra are all just arithmetic on that one number -
  there's no separate "nakshatra API" to call. That's most of what this
  file does.
"""

import swisseph as swe

from app.models.chart import BirthDetails, PlanetPosition

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

PLANET_CODES = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,  # lunar north node
}

NAKSHATRA_SPAN = 360.0 / 27.0     # 13.3333... degrees
PADA_SPAN = NAKSHATRA_SPAN / 4.0  # 3.3333... degrees


def _to_julian_day_ut(birth: BirthDetails) -> float:
    """Convert local birth date/time + timezone offset into Julian Day (UT)."""
    year, month, day = (int(x) for x in birth.date.split("-"))
    hour, minute = (int(x) for x in birth.time.split(":"))
    local_decimal_hour = hour + minute / 60.0
    ut_decimal_hour = local_decimal_hour - birth.timezone_offset_hours
    return swe.julday(year, month, day, ut_decimal_hour)


def sign_from_longitude(longitude: float) -> str:
    return SIGNS[int(longitude // 30) % 12]


def nakshatra_from_longitude(longitude: float) -> tuple[str, int]:
    index = int(longitude // NAKSHATRA_SPAN) % 27
    position_within = longitude % NAKSHATRA_SPAN
    pada = int(position_within // PADA_SPAN) + 1
    return NAKSHATRAS[index], pada


def _house_from_sign(planet_sign_index: int, ascendant_sign_index: int) -> int:
    """Whole-sign house system: house 1 = ascendant's sign, counting forward."""
    return ((planet_sign_index - ascendant_sign_index) % 12) + 1


def compute_positions(birth: BirthDetails) -> tuple[list[PlanetPosition], str]:
    """Returns (planet positions, ascendant sign) - the two raw ingredients
    dasha.py and panchang.py need. Assembly into a full ComputedChart happens
    in compute/chart_builder.py, once dasha and panchang are also available."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    jd_ut = _to_julian_day_ut(birth)
    sidereal_flag = swe.FLG_SIDEREAL | swe.FLG_SPEED

    # Ascendant (Lagna): whole-sign house system needs only the ascendant's
    # sign, which we get from the sidereal cusp calculation.
    cusps, ascmc = swe.houses_ex(jd_ut, birth.latitude, birth.longitude, b"W", flags=sidereal_flag)
    ascendant_longitude = ascmc[0]
    ascendant_sign_index = int(ascendant_longitude // 30) % 12

    positions = []
    for planet_name, code in PLANET_CODES.items():
        (longitude, _lat, _dist, speed, *_), _flags = swe.calc_ut(jd_ut, code, sidereal_flag)
        sign = sign_from_longitude(longitude)
        nakshatra, pada = nakshatra_from_longitude(longitude)
        sign_index = SIGNS.index(sign)
        house = _house_from_sign(sign_index, ascendant_sign_index)

        positions.append(PlanetPosition(
            planet=planet_name,
            longitude_degrees=round(longitude, 4),
            sign=sign,
            house=house,
            nakshatra=nakshatra,
            nakshatra_pada=pada,
            is_retrograde=speed < 0,
        ))

    # Ketu is always exactly 180 degrees from Rahu - not an independent body.
    rahu = next(p for p in positions if p.planet == "Rahu")
    ketu_longitude = (rahu.longitude_degrees + 180) % 360
    ketu_sign = sign_from_longitude(ketu_longitude)
    ketu_nakshatra, ketu_pada = nakshatra_from_longitude(ketu_longitude)
    positions.append(PlanetPosition(
        planet="Ketu",
        longitude_degrees=round(ketu_longitude, 4),
        sign=ketu_sign,
        house=_house_from_sign(SIGNS.index(ketu_sign), ascendant_sign_index),
        nakshatra=ketu_nakshatra,
        nakshatra_pada=ketu_pada,
        is_retrograde=True,  # Rahu/Ketu are always treated as retrograde in Vedic astrology
    ))

    ascendant_sign = SIGNS[ascendant_sign_index]
    return positions, ascendant_sign
