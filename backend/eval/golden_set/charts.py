"""
A small, fixed set of birth charts used to measure hallucination rate
consistently across runs. Deliberately diverse - different decades,
hemispheres, and times of day - so the eval isn't accidentally tuned to
one narrow kind of chart.

Kept small (5) for phase 3 so a full eval run is fast and cheap to
iterate on. Expanding this set is the easiest way to make the resulting
hallucination-rate number more statistically credible, once the harness
itself is confirmed working end to end.
"""

from app.models.chart import BirthDetails

GOLDEN_SET: list[BirthDetails] = [
    BirthDetails(date="1998-04-12", time="14:35", latitude=25.59, longitude=85.13, timezone_offset_hours=5.5),   # Patna, India
    BirthDetails(date="1990-11-03", time="06:20", latitude=28.6139, longitude=77.2090, timezone_offset_hours=5.5),  # Delhi, India
    BirthDetails(date="2003-07-19", time="22:10", latitude=19.0760, longitude=72.8777, timezone_offset_hours=5.5),  # Mumbai, India
    BirthDetails(date="1985-01-27", time="11:45", latitude=40.7128, longitude=-74.0060, timezone_offset_hours=-5.0),  # New York, USA
    BirthDetails(date="2015-09-05", time="03:55", latitude=51.5074, longitude=-0.1278, timezone_offset_hours=0.0),   # London, UK
]
