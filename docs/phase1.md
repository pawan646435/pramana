# Phase 1 — the ground truth layer, for real

Phase 0 was the shape of the system. Phase 1 fills in `compute/` with
actual astronomical calculation. Everything here was run and verified,
not just written — the numbers you see in the examples below came from
real function calls in this sandbox.

## What got built

- **`compute/ephemeris.py`** — planetary positions via `pyswisseph`
- **`compute/dasha.py`** — Vimshottari dasha timeline
- **`compute/panchang.py`** — today's tithi/yoga/karana/nakshatra
- **`compute/chart_builder.py`** — combines all three into one `ComputedChart`
- **`api/routes/chart.py`** — a real `POST /api/charts/compute` endpoint

## The concepts, and why the code is shaped this way

### 1. Sidereal vs tropical — one line of setup, big consequence

`swe.set_sid_mode(swe.SIDM_LAHIRI)` in `ephemeris.py` is the single most
important line in the file. Without it, Swiss Ephemeris defaults to the
*tropical* zodiac (season-based — what Western astrology uses). Vedic
astrology uses the *sidereal* zodiac (actual fixed-star positions).
Precession has drifted the two about 24 degrees apart today. Forget this
line, and every sign placement in the whole system is subtly wrong in a
way that would be very easy to miss during testing, since the chart
would still *look* plausible.

### 2. Everything downstream is arithmetic on one number

Swiss Ephemeris only gives you raw longitude (0–360°). Sign, nakshatra,
and house are all just slicing that number differently:

```python
sign = SIGNS[int(longitude // 30) % 12]                  # 12 signs, 30° each
nakshatra_index = int(longitude // NAKSHATRA_SPAN) % 27   # 27 nakshatras, 13.33° each
```

There's no separate "nakshatra API" — recognizing that it's all the same
underlying number, sliced at different resolutions, is most of what
makes this module simple instead of complicated.

### 3. Vimshottari dasha: fixed ratios, personalized start point

The 120-year cycle and its 9 lords are fixed by the system's definition
— that part never changes. What's personal to *your* chart is only:
which nakshatra the Moon sat in at birth (determines the starting lord),
and how far through that nakshatra the Moon already was (determines the
"balance" — how much of that first lord's period is left to run from
birth). Verified example, born 1998-04-12 with Moon in Chitra nakshatra:

```
Mars     1998-04-12 -> 2000-01-22   (partial - balance of dasha at birth)
Rahu     2000-01-22 -> 2018-01-21
Jupiter  2018-01-21 -> 2034-01-21
...
```

Chitra is ruled by Mars in the fixed nakshatra-lord mapping, so Mars
starts the sequence — but only for the remaining balance, not a full 7
years, because the Moon was already partway through Chitra at birth.

### 4. Antardasha is the same math, one level down

`compute_antardashas()` doesn't run a new calculation — it takes one
Mahadasha's date range and splits it proportionally using the exact same
9-lord ratios, starting from the Mahadasha's own lord. Same fixed ratios,
applied recursively. This is why the function is ~15 lines: once you see
the pattern, there's nothing new to compute.

### 5. Where phase 1 cuts corners — and why that's stated, not hidden

Two simplifications are documented directly in `panchang.py`'s docstring:

- Panchang is computed at midnight UT, not local sunrise. The Vedic day
  technically starts at sunrise, so a value that changes right around
  sunrise could show as the previous day's reading. Fixing this needs
  `swe.rise_trans()` to find actual local sunrise — a good phase 2 task.
- Karana has 4 "fixed" special-case names mixed into an otherwise
  repeating 7-name cycle. The repeating cycle is implemented exactly;
  the 4 fixed cases are approximated by position rather than exactly
  pinned.

Both are flagged in code comments rather than silently smoothed over.
That's not an accident — a project whose entire premise is "don't
fabricate precision you don't have" should not fabricate precision in
its own ground-truth layer either.

## What's still deferred

- Sunrise-accurate panchang (`swe.rise_trans`)
- Exact fixed-karana positioning
- `generation/` — prompt templates + Groq/Gemini clients that read
  `ComputedChart` and produce narrative text
- `verification/` — claim extraction + grounding check against
  `ComputedChart`
- Postgres persistence (`db/`) — right now `build_chart()` computes
  fresh every call; nothing is stored yet
- The eval harness (`eval/`) that will produce the real hallucination-rate number

## Try it

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# then, in another terminal:
curl -X POST http://localhost:8000/api/charts/compute \
  -H "Content-Type: application/json" \
  -d '{"date":"1998-04-12","time":"14:35","latitude":25.59,"longitude":85.13,"timezone_offset_hours":5.5}'
```
