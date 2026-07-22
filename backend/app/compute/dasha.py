"""
Vimshottari dasha - a 120-year cycle divided among 9 planetary lords in a
fixed order, with fixed year-lengths per lord. Entirely deterministic:
given the Moon's nakshatra and exact position at birth, the whole
sequence for a lifetime is fixed algebra, not interpretation.

RULE: no LLM calls in this file. See compute/ephemeris.py for why.
"""

from datetime import datetime, timedelta

from app.models.chart import DashaPeriod, PlanetPosition
from app.compute.ephemeris import NAKSHATRAS, NAKSHATRA_SPAN

DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
TOTAL_CYCLE_YEARS = sum(DASHA_YEARS.values())  # 120, by construction of the system
DAYS_PER_YEAR = 365.25  # standard convention used across Vimshottari software


def _nakshatra_ruling_lord(nakshatra: str) -> str:
    """Each of the 27 nakshatras is pre-assigned a lord, cycling through
    DASHA_ORDER three times (27 = 9 * 3). This mapping is fixed by the
    system's definition, not computed from planetary motion."""
    index = NAKSHATRAS.index(nakshatra)
    return DASHA_ORDER[index % 9]


def compute_mahadashas(moon: PlanetPosition, birth_date: str) -> list[DashaPeriod]:
    """
    Returns the sequence of Mahadasha (level 1) periods from birth onward,
    covering one full remaining cycle. The first period is partial - only
    the "balance" of the birth nakshatra's lord remains, proportional to
    how far the Moon had already travelled through that nakshatra.
    """
    year, month, day = (int(x) for x in birth_date.split("-"))
    birth_dt = datetime(year, month, day)

    starting_lord = _nakshatra_ruling_lord(moon.nakshatra)
    starting_index = DASHA_ORDER.index(starting_lord)

    fraction_elapsed = (moon.longitude_degrees % NAKSHATRA_SPAN) / NAKSHATRA_SPAN

    periods: list[DashaPeriod] = []
    current_start = birth_dt

    for i in range(9):
        lord = DASHA_ORDER[(starting_index + i) % 9]
        full_years = DASHA_YEARS[lord]
        duration_years = full_years * (1 - fraction_elapsed) if i == 0 else full_years
        current_end = current_start + timedelta(days=duration_years * DAYS_PER_YEAR)

        periods.append(DashaPeriod(
            lord=lord,
            start_date=current_start.date().isoformat(),
            end_date=current_end.date().isoformat(),
            level=1,
        ))
        current_start = current_end

    return periods


def compute_antardashas(mahadasha: DashaPeriod) -> list[DashaPeriod]:
    """
    Subdivides one Mahadasha into its 9 Antardasha (level 2) sub-periods.
    Same fixed 9-lord order, starting from the Mahadasha's own lord, each
    sub-period's length is proportional to (that lord's years / 120) of
    the Mahadasha's total duration - not a separate calculation, just a
    proportional split of the same fixed ratios.
    """
    start = datetime.fromisoformat(mahadasha.start_date)
    end = datetime.fromisoformat(mahadasha.end_date)
    total_days = (end - start).days

    starting_index = DASHA_ORDER.index(mahadasha.lord)
    periods: list[DashaPeriod] = []
    current_start = start

    for i in range(9):
        lord = DASHA_ORDER[(starting_index + i) % 9]
        proportion = DASHA_YEARS[lord] / TOTAL_CYCLE_YEARS
        duration_days = total_days * proportion
        current_end = current_start + timedelta(days=duration_days)

        periods.append(DashaPeriod(
            lord=lord,
            start_date=current_start.date().isoformat(),
            end_date=current_end.date().isoformat(),
            level=2,
        ))
        current_start = current_end

    return periods


def get_current_dashas(moon: PlanetPosition, birth_date: str, as_of: datetime | None = None) -> list[DashaPeriod]:
    """The one function callers actually use: current Mahadasha + its
    active Antardasha, as of today (or a given date)."""
    as_of = as_of or datetime.now()
    mahadashas = compute_mahadashas(moon, birth_date)

    active_maha = next(
        (m for m in mahadashas
         if datetime.fromisoformat(m.start_date) <= as_of <= datetime.fromisoformat(m.end_date)),
        mahadashas[-1],  # fallback: person is older than the computed window
    )
    antardashas = compute_antardashas(active_maha)
    active_antar = next(
        (a for a in antardashas
         if datetime.fromisoformat(a.start_date) <= as_of <= datetime.fromisoformat(a.end_date)),
        antardashas[-1],
    )

    return [active_maha, active_antar]
