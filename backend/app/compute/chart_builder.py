"""
The only file that imports from ephemeris.py, dasha.py, and panchang.py
together. Everything above this stays independently testable; this file
just wires the three ground-truth sources into one ComputedChart object,
which is what generation/ and verification/ will consume.

RULE: no LLM calls in this file either - assembly of ground truth is
still ground truth.
"""

from datetime import datetime, timezone, date

from app.models.chart import BirthDetails, ComputedChart
from app.compute.ephemeris import compute_positions
from app.compute.dasha import get_current_dashas
from app.compute.panchang import compute_panchang


def build_chart(birth: BirthDetails) -> ComputedChart:
    positions, _ascendant_sign = compute_positions(birth)
    moon = next(p for p in positions if p.planet == "Moon")

    current_dashas = get_current_dashas(moon, birth.date)
    panchang_today = compute_panchang(date.today())

    return ComputedChart(
        birth_details=birth,
        computed_at=datetime.now(timezone.utc),
        positions=positions,
        current_dashas=current_dashas,
        panchang_today=panchang_today,
    )
