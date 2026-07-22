"""
Schemas for the deterministic ground-truth layer.

Everything in this file describes data produced by compute/ — real
astronomical calculation, never an LLM. If a field can't ultimately be
traced to a swisseph call or a documented panchang rule, it doesn't
belong in this file.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class BirthDetails(BaseModel):
    date: str = Field(..., description="ISO date, e.g. 1998-04-12")
    time: str = Field(..., description="Local time, 24h, e.g. 14:35")
    latitude: float
    longitude: float
    timezone_offset_hours: float = Field(..., description="e.g. 5.5 for IST")


class PlanetPosition(BaseModel):
    planet: str
    longitude_degrees: float
    sign: str
    house: int
    nakshatra: str
    nakshatra_pada: int
    is_retrograde: bool


class DashaPeriod(BaseModel):
    lord: str
    start_date: str
    end_date: str
    level: int = Field(..., description="1 = Mahadasha, 2 = Antardasha, etc.")


class PanchangDay(BaseModel):
    date: str
    tithi: str
    nakshatra: str
    yoga: str
    karana: str
    moon_sign: str
    sun_sign: str


class ComputedChart(BaseModel):
    """
    The single source of ground truth for one birth chart.
    Every claim the generation layer makes must be traceable to a field
    in this object — that traceability is what verification/ checks.
    """
    birth_details: BirthDetails
    computed_at: datetime
    positions: list[PlanetPosition]
    current_dashas: list[DashaPeriod]
    panchang_today: PanchangDay
