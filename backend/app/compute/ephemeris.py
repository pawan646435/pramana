"""
Deterministic astronomical computation.

RULE: nothing in this module or its neighbors (dasha.py, panchang.py,
to be added in phase 1) may import from app.generation or app.verification,
and no function here may call an LLM. This is the ground truth layer —
its whole value is that it cannot hallucinate. If that invariant breaks,
the project's core claim breaks with it.

Phase 0: interface only. Real swisseph calls land in phase 1.
"""

from app.models.chart import BirthDetails, ComputedChart


def compute_chart(birth_details: BirthDetails) -> ComputedChart:
    """
    Phase 1 will implement this using pyswisseph:
      - swe.set_topo() for the birth location
      - swe.calc_ut() per planet for longitude -> sign, house, nakshatra
      - a documented vimshottari dasha algorithm for current_dashas
      - a documented panchang algorithm for panchang_today

    Raising here deliberately, so nothing downstream can accidentally
    run against fabricated placeholder data.
    """
    raise NotImplementedError("Phase 1: wire up pyswisseph in compute/ephemeris.py")
