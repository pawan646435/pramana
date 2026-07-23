# Pramana

**Sanskrit: "a valid means of knowledge" — a proof standard.**

A hallucination-grounded generation system for Vedic astrology charts. A
deterministic computation engine produces verified astronomical ground
truth; an LLM narrative layer generates text constrained to only what's
traceable in that computed output; a verification pipeline checks every
generated claim against the source data before it reaches the user.

Vedic astrology is the domain, chosen deliberately: it's one of the few
domains where "ground truth" is fully computable (planetary positions,
dashas, panchang), which makes hallucination rate a *measured* number
instead of an assumed one.

## Live

- **App**: [pramana-astro.vercel.app](https://pramana-astro.vercel.app)
- **API**: [pramana-7lzf.onrender.com](https://pramana-7lzf.onrender.com)

> The backend runs on Render's free tier, which spins down after 15
> minutes of inactivity. If the app feels slow on first load, that's a
> cold start (30–60s) waking the API back up — not a bug.

## The measured result

Ran the eval harness (5 diverse birth charts, ungrounded vs. grounded
generation, both verified against the same real computed chart) against
Groq's Llama 3.3 70B:

| Condition | Hallucination rate |
|---|---|
| Ungrounded (no computed data given) | 39.6% |
| Grounded (Pramana's full pipeline) | 0.0% |
| **Relative reduction** | **100%** |

This is a real, run, measured number — not an estimate. See
[`docs/phase3.md`](docs/phase3.md) for the eval harness design and how
to reproduce it.

## Architecture

```
backend/app/
  compute/       deterministic layer — ephemeris, dasha, panchang.
                 No LLM calls. Ever.
  generation/     LLM narrative layer — Groq + Gemini clients,
                 grounding-constrained prompts
  verification/   claim extraction + rule-based checks + LLM-judge
                 fallback, checked against compute/ output
  models/         pydantic schemas shared across layers
  db/             Postgres persistence (SQLAlchemy async) +
                 Redis caching (chart cache + history cache)
  api/routes/     FastAPI endpoints

frontend/
  app/            Next.js App Router — landing page (3D solar system)
                 + dashboard
  components/     Hero3DScene (Three.js), HistorySection,
                 CssStarfield, expand/collapse cards
  lib/api.ts      typed client matching backend schemas field-for-field

eval/             golden-set eval harness (ungrounded vs. grounded)
```

**The one architectural rule that matters most**: `compute/` never
imports from `generation/` or `verification/`, and never calls an LLM.
That's the whole premise — the ground-truth layer has to be incapable
of hallucinating, or the entire grounding claim collapses.

## What it actually does

- **Real astronomical computation** via `pyswisseph`: sidereal
  (Lahiri ayanamsa) planetary positions, Vimshottari dasha timeline,
  daily panchang — all deterministic, zero LLM involvement
- **Grounded narrative generation** via Groq or Gemini, constrained by
  a prompt that forbids inventing placements or using unearned
  subjective language ("rare," "powerful") not backed by data
- **Claim-level verification**: every generated sentence is split into
  atomic claims, checked against the computed chart via fast
  rule-based matching first, falling back to an LLM judge only for
  claims rules can't resolve
- **A 3D interactive landing page**: real-time Three.js solar system
  with procedurally textured planets, drag-to-orbit interaction,
  hover/tap-for-facts, a custom cursor, and mobile-optimized touch
  handling
- **A live dashboard**: run the eval harness for real, try your own
  birth chart, browse history of past runs and generations — all
  backed by real Postgres persistence and Redis caching
- **Caching with a hard correctness guarantee**: Redis caches
  deterministic chart computations and recent-history reads, but every
  cache read/write fails soft — a Redis or Postgres outage degrades
  performance, never correctness

## Tech stack

**Backend**: FastAPI · PostgreSQL (Neon) · Redis (Upstash) · SQLAlchemy
2.0 (async) · Alembic · pyswisseph · Groq (Llama 3.3 70B) · Gemini ·
Docker Compose (local dev)

**Frontend**: Next.js 15 · TypeScript · Tailwind CSS · Three.js ·
Framer Motion

**Deployment**: Render (backend) · Vercel (frontend) · Neon (managed
Postgres) · Upstash (managed Redis)

## Project history

Built in phases, each with a written teaching doc covering what was
built, why, and what was verified:

- [`docs/phase0.md`](docs/phase0.md) — scaffolding, schemas, tooling
- [`docs/phase1.md`](docs/phase1.md) — real ephemeris/dasha/panchang computation
- [`docs/phase2.md`](docs/phase2.md) — generation + verification pipeline
- [`docs/phase3.md`](docs/phase3.md) — the eval harness and the real measured number
- [`docs/phase4.md`](docs/phase4.md) — the Next.js frontend
- [`docs/phase5.md`](docs/phase5.md) — Redis caching + Postgres persistence

A few real bugs were caught and fixed along the way rather than
papered over — a natal-vs-transit contradiction in claim verification,
an event-loop binding bug in an early Redis client pattern, a
timezone-naive timestamp bug affecting displayed history dates, and a
CORS gap discovered only once the frontend and backend were actually
wired together. Each is documented in its corresponding phase doc.

## Running it locally

**Backend:**
```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your own Groq/Gemini keys, DB URLs
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL
npm run dev
```

**Local Postgres + Redis** (or use your own managed instances):
```bash
docker compose up -d postgres
# Redis: brew install redis && brew services start redis
```

## Known limitations

Documented honestly rather than hidden:

- Panchang is computed at midnight UT rather than local sunrise (the
  technically correct Vedic-day boundary) — see `docs/phase1.md`
- Karana's 4 fixed special cases are approximated rather than exactly
  pinned within the lunar month
- The eval harness's golden set is 5 charts — enough to demonstrate the
  method, not yet enough for strong statistical confidence at scale
- No live device testing for mobile — touch/gesture behavior was
  verified via Playwright emulation, not physical iOS/Android hardware

---

*Named after the Sanskrit term for a valid means of knowledge — because
that's the property this system is built to guarantee: every generated
claim traces to a verified source, not an invented one.*
