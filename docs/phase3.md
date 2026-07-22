# Phase 3 — the eval harness: turning "grounded" into a measured number

Everything before this phase built the machinery. This phase is the
actual payoff: the thing that turns "we built a grounding system" into
"here's the measured hallucination rate, before and after."

## The core idea

For each chart in a fixed golden set, generate two narratives with the
*same* model and *same* birth details:

- **Ungrounded**: the model gets only birth date/time/place and is asked
  to write a reading including specific placements, dasha, and panchang
  - with no computed data. Whatever specifics it states, it invented.
- **Grounded**: the existing phase 2 pipeline - real `ComputedChart`
  handed to the model, constrained prompt.

Both narratives get checked by the *exact same verifier* against the
*exact same real chart*. That symmetry is the whole point: the
comparison is fair because nothing about the grading changes between
conditions, only what the generator had to work with.

## What got built

- **`generation/prompts.py`** — added `UNGROUNDED_SYSTEM_PROMPT` and
  `build_ungrounded_prompt()`, deliberately giving the model nothing to
  ground itself in
- **`generation/generator.py`** — added `generate_ungrounded_narrative()`
  alongside the existing grounded generator
- **`eval/golden_set/charts.py`** — 5 diverse test charts (different
  decades, hemispheres, times of day)
- **`models/eval.py`** — `EvalCase` (one chart's two results) and
  `EvalReport` (aggregated across the golden set), with
  `avg_ungrounded_hallucination_rate`, `avg_grounded_hallucination_rate`,
  and `relative_reduction` as computed fields
- **`eval/harness.py`** — runs both conditions across the golden set
- **`eval/scripts/run_eval.py`** — CLI runner, saves results to JSON
- **`api/routes/eval.py`** — `POST /api/eval/run` for the dashboard

## A structural note: eval/ moved inside backend/

The original phase 0 scaffold had `eval/` as a sibling of `backend/` at
the project root. Phase 3 moved it to `backend/eval/` instead. Reason:
the harness needs to import `app.models.chart`, `app.compute.chart_builder`,
etc. directly - that only works cleanly when `eval/` sits inside the same
Python package tree as `app/`, importable from the same working directory
you already run `uvicorn` from. Keeping them siblings at the project root
would have meant fragile `sys.path` manipulation to reach across. This is
a minor reorganization, not a design change - worth knowing so old notes
referencing a top-level `eval/` folder aren't confusing later.

## `relative_reduction`: guarding a real edge case

If a model ever produces a perfectly grounded ungrounded-condition
narrative (rate = 0.0), computing `(ungrounded - grounded) / ungrounded`
would divide by zero. `relative_reduction` checks for that and returns
0.0 instead of crashing - correctly interpreted as "nothing to reduce,"
not an error state.

## Verified with mocked generation (harness math, confirmed correct)

Ran the harness against 2 test charts with a fake ungrounded narrative
(wrong house + an unearned "rare" claim) and a fake grounded narrative
(correct house for one chart, coincidentally wrong for the other, since
the mock used identical text for both charts rather than a real
per-chart response):

```
avg_ungrounded_hallucination_rate: 1.0
avg_grounded_hallucination_rate:   0.5
relative_reduction:                0.5
```

The math checks out ((1.0 - 0.5) / 1.0 = 0.5), and the harness correctly
computed a *different* result per chart based on each chart's own real
ground truth rather than assuming one shared answer - confirmed by the
grounded condition being right for chart 1 and wrong for chart 2, purely
because the mock's fixed text didn't match chart 2's real Mars house.
Also confirmed: an empty case list returns 0.0 everywhere rather than
crashing on division by zero.

## What to run on your machine for the real number

```bash
cd backend
python -m eval.scripts.run_eval groq
```

This makes 10 real API calls (5 charts x 2 conditions) - costs a small
amount and takes a minute or two. It'll print the real
avg_ungrounded/avg_grounded/relative_reduction numbers and save the full
report to `eval/results.json`.

Or via the API, same as the dashboard would call it:

```bash
curl -X POST "http://localhost:8000/api/eval/run?provider=groq"
```

**What to actually look at once you have real numbers:**
- Is `avg_ungrounded_hallucination_rate` meaningfully above zero? If
  Groq's ungrounded condition happens to hedge heavily ("your Mars
  placement, whatever it may be...") rather than stating specifics, the
  baseline might look artificially low - worth reading a few raw
  ungrounded narratives to check they're actually attempting specific
  claims, not dodging the question.
- Is `avg_grounded_hallucination_rate` close to zero? If it isn't,
  that's real signal the prompt constraints from phase 2 need
  tightening, not a report you should round away.

## What's still deferred

- Expanding the golden set beyond 5 charts for more statistical weight
- Persisting eval runs over time in Postgres, so the dashboard can show
  a trend rather than only the latest run
- Testing Gemini as well as Groq and comparing the two (the frontend
  mockup's "model comparison" panel wants exactly this data)
