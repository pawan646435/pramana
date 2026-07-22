# Phase 0 — scaffolding, schemas, tooling config

## What got built and why

### 1. The folder structure encodes the architecture

`compute/`, `generation/`, `verification/` aren't just organization —
they're the three claims your resume bullet makes, turned into code
boundaries:

- **compute/** — deterministic. No randomness, no LLM, same input always
  gives same output. This is what makes "ground truth" a meaningful
  phrase instead of marketing language.
- **generation/** — the LLM narrative layer. Reads compute output,
  produces natural language. Never invents fields that aren't there.
- **verification/** — checks generation output against compute output.
  This is the auditor pattern from Veritas, applied here.

The rule stated in `compute/ephemeris.py`'s docstring — no imports from
generation or verification, no LLM calls, ever — is the single most
important line in the whole scaffold. Everything downstream depends on
this layer being incapable of hallucinating.

### 2. Why schemas came before any real logic

`models/chart.py` and `models/verification.py` define the data
*contracts* before a single ephemeris calculation exists. This forces a
concrete answer to a question that's easy to hand-wave: **what exactly
counts as a "grounded claim"?**

The answer baked into the schema: a claim is grounded only if it can be
traced to a specific field path in `ComputedChart` (see
`grounded_field_path` in `VerifiedClaim`). If verification can't point
to a field, the claim is either `unverifiable` (interpretive, not meant
to be checked) or `ungrounded` (flagged). There's no fourth option where
you just trust the model — that ambiguity is exactly what you're trying
to engineer out.

### 3. `hallucination_rate` is a computed property, not a stored number

Look at `GenerationResult.hallucination_rate` in `models/verification.py`
— it's derived directly from the ratio of `ungrounded` claims to total
claims. This means the number in your resume bullet ("4.2% → 0.3%")
will come from running this property over a real eval set, not from an
estimate. That's the difference this project is supposed to demonstrate.

### 4. Why `compute_chart()` raises `NotImplementedError` right now

It would be easy to stub this out with fake return data so the API
"works" end to end today. Deliberately not doing that: if something
downstream (generation, an early frontend demo) accidentally runs
against placeholder data, you want a loud failure, not a silently wrong
chart. Phase 1 replaces this with real `pyswisseph` calls.

## What's explicitly deferred to phase 1

- Real ephemeris computation (`compute/ephemeris.py`)
- Dasha and panchang algorithms (`compute/dasha.py`, `compute/panchang.py`)
- Prompt templates + Groq/Gemini clients (`generation/`)
- Claim extraction (splitting narrative text into checkable units) and
  the grounding-check logic itself (`verification/`)
- Postgres models + Alembic migrations (`db/`)
- The eval harness and golden set (`eval/`)

## How to run what exists today

```bash
cd backend
cp .env.example .env
docker compose up --build
curl http://localhost:8000/health
```
