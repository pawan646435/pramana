# Phase 2 — generation and verification, the actual novel part

Phase 1 built ground truth. Phase 2 builds the two layers that make
Pramana's actual pitch real: narrative generation constrained to that
ground truth, and a verification pipeline that checks whether the model
actually stayed constrained.

Everything below was run and verified in this environment except the
live Groq/Gemini API calls themselves, which need your real keys - those
are the one piece you'll test on your machine. Everything else (rule
engine, claim extraction, full pipeline wiring) was tested here with a
mocked LLM response standing in for the real call.

## What got built

- **`generation/prompts.py`** — the system prompt that does the actual
  grounding work: explicit rules against inventing placements and
  against unearned subjective language ("rare", "powerful")
- **`generation/clients.py`** — thin Groq/Gemini wrappers
- **`generation/generator.py`** — orchestrates prompt + provider call
- **`verification/claim_extractor.py`** — splits narrative into
  sentence-level claims
- **`verification/rules.py`** — fast, free, deterministic checks against
  `ComputedChart`
- **`verification/llm_judge.py`** — LLM fallback for claims rules can't
  resolve
- **`verification/verifier.py`** — orchestrates extraction → rules →
  judge fallback → `GenerationResult`
- **`api/routes/generate.py`** — `POST /api/generate/narrative`

## The design decision that matters most: rules before judge

`verify_narrative()` always tries `check_rules()` first. The LLM judge
only runs when rules return `(None, None, 0.0)` - genuinely undecided.
This isn't just a cost optimization, though it is that too. It's also a
correctness argument: a regex check against a JSON field is
*deterministic* - it either matches or it doesn't, with zero variance
run to run. An LLM judge, even a good one, has some irreducible variance.
Minimizing how much of your grounding claim rests on the variance-prone
path is the more defensible position when someone asks "how do you know
your verification pipeline itself isn't hallucinating."

## Verified behavior (real test run, mocked LLM response)

Fed the verifier a narrative with a deliberate mix of true, false, and
vague claims, checked against the real chart from phase 1:

```
grounded    Your Moon sits in the Chitra nakshatra...        (true - matches chart)
grounded    You are currently in the Jupiter Mahadasha...    (true - matches chart)
ungrounded  Mars is placed in the 3rd house...                (false - chart says house 9)
ungrounded  This is an extremely rare planetary alignment...  (unearned intensifier)
unverifiable You may find this a meaningful time...           (no chart-checkable content)

hallucination_rate: 0.4
```

The second "ungrounded" result is the one worth sitting with: the rule
engine didn't just fail to confirm that claim, it actively caught a
*contradiction* - the claim said house 3, the real chart says house 9.
That's the difference between "we couldn't verify this" and "this is
wrong," and only the second one is a real hallucination catch.

## Why `hallucination_rate` needed a one-line fix

It was originally a plain Python `@property` on the pydantic model,
which computes correctly in Python but doesn't automatically appear in
the JSON a FastAPI endpoint returns - pydantic only serializes declared
fields by default. Wrapping it with `@computed_field` tells pydantic to
include it in serialization. Caught by actually hitting the API endpoint
and inspecting the response, not by reading the code - a good example of
why "it imports without errors" and "it works end to end" are different
bars to clear.

## What to test on your machine

Your Groq and Gemini keys go in `backend/.env`. Once they're in:

```bash
curl -X POST "http://localhost:8000/api/generate/narrative?provider=groq" \
  -H "Content-Type: application/json" \
  -d '{"date":"1998-04-12","time":"14:35","latitude":25.59,"longitude":85.13,"timezone_offset_hours":5.5}'
```

Things worth checking with real output:
- Does the model actually follow the "no unearned intensifiers" rule, or
  does it slip in "powerful"/"rare" anyway? If it does, that's real
  signal for tightening the prompt.
- Does `judge_claim()` return clean, parseable JSON consistently, or does
  it sometimes wrap the JSON in markdown fences? If the latter, the
  `except (json.JSONDecodeError, ...)` fallback in `llm_judge.py` will
  quietly mark those as unverifiable rather than crash - worth checking
  how often that happens, since a high fallback rate would mean the
  judge prompt needs a stricter output constraint.

## Update: compound-claim splitting

Originally, a sentence like "The Moon in the 3rd house often relates to
communication" was checked as one claim - the interpretive tail rode
along on the factual head's verdict, so a true placement plus vague
commentary both came back "grounded" together, even though only the
first half was actually checkable.

`claim_extractor.py` now splits on a fixed list of known interpretive
connector phrases ("often relates to", "which suggests", "often
associated with", etc.), producing two separate claims from one
sentence: the factual clause (checked normally against `ComputedChart`)
and the interpretive clause (correctly falls through to `unverifiable`
rather than inheriting the factual clause's grounded status).

Verified against the real sentence from a live Groq response:

```
Before fix:  1 claim  -> grounded (blended verdict)
After fix:   2 claims -> grounded (the placement) + unverifiable (the commentary)
```

## Update: checking all facts in a claim, not just the first

`check_rules()` originally returned as soon as it found one matching
fact - a claim bundling several facts ("Moon in Libra and Sun in Cancer,
tithi Navami, nakshatra Swati") only had its first fact actually
checked; the rest rode along unverified. Fixed to collect every matching
fact in the claim and only report grounded if all of them check out
(ungrounded if any single one contradicts the data).

This surfaced a real trap worth understanding: the same planet name
(Sun, Moon) appears in two different places in `ComputedChart` - the
natal `positions` (birth placement) and `panchang_today` (today's
transit). For this test chart, natal Sun sign is Pisces but today's
transiting Sun sign is Cancer - both true, about different things. A
naive "check every fact" implementation would compare "Sun in Cancer"
against the *natal* Sun position and wrongly flag it as a contradiction.

Fixed by checking panchang fields first and recording which (planet,
sign) pairs got confirmed as *today's transit* before running the natal
position loop; the natal loop skips flagging a contradiction for a sign
that was already confirmed via panchang for that same planet. Verified
against the real narrative from a live Groq run - the panchang sentence
now correctly grounds with `panchang_today.sun_sign` in its path, no
false contradiction against `positions[0].sign` (Pisces).


## What's still deferred

- Postgres persistence (`db/`) - results aren't stored yet, only returned
- The golden-set eval harness (`eval/`) - the real ungrounded-vs-grounded
  baseline comparison that produces your resume's X%→Y% number

