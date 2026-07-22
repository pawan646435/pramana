# Pramana

**Sanskrit: "a valid means of knowledge" — a proof standard.**

Pramana is a hallucination-grounded generation system. A deterministic
computation engine produces verified astronomical ground truth; an LLM
narrative layer generates text constrained to only what's traceable in
that computed output; a verification pass checks every generated claim
against the source data before it reaches the user.

Vedic astrology is the domain, chosen deliberately: it is one of the few
domains where "ground truth" is fully computable (planetary positions,
dashas, panchang), which means hallucination rate can be measured
precisely rather than asserted.

## Architecture

```
backend/app/
  compute/       deterministic layer — ephemeris, dasha, panchang. No LLM calls. Ever.
  generation/     LLM narrative layer — Groq + Gemini clients, prompt templates
  verification/   claim extraction + grounding check against compute/ output
  models/         pydantic schemas shared across layers
  db/             postgres models + session
  api/routes/     FastAPI endpoints
```

The architectural rule that matters: **compute/ never imports generation/
or verification/, and never calls an LLM.** If it did, the ground truth
layer could itself become a source of hallucination, which defeats the
entire premise of the project.

## Status

Phase 0 — scaffolding, schemas, tooling config. See `docs/phase0.md`.

## Stack

FastAPI · PostgreSQL · Redis · pyswisseph · Groq (Llama 3.3 70B) · Gemini ·
Docker · Next.js (frontend, separate)
