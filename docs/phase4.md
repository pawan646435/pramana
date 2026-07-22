# Phase 4 — the frontend, wired to real data

Everything before this phase was backend. This phase builds the actual
Next.js app someone would click through - the landing page with the 3D
scene, and a dashboard that shows real numbers from your real backend,
not the hardcoded mockup numbers from the original HTML prototypes.

Verified in this environment: `npm install`, `npm run build` (clean
compile, TypeScript strict mode passing, both routes statically
generated), and `npm run dev` serving real HTML on both routes. What I
can't verify here is the actual live data flowing through - that needs
your backend running and your API keys, same as every LLM-touching piece
so far.

## What got built

- **`app/page.tsx`** — landing page: 3D scene + hero copy + nav
- **`components/Hero3DScene.tsx`** — the Three.js scene, ported from the
  standalone HTML mockup into a proper React client component
- **`app/dashboard/page.tsx`** — the real dashboard: live eval runner,
  a "try it yourself" form hitting real generation, today's panchang
  fact card
- **`lib/api.ts`** — typed client for every backend endpoint, matching
  the actual pydantic schemas field-for-field
- **New backend endpoint**: `GET /api/charts/panchang/today` - added
  specifically so the fact card can show something real without needing
  birth details or an LLM call

## The mockup vs. this: what changed, and why

The original HTML mockups (built early in this project, before any
backend existed) had a "Groq vs Gemini" model-comparison panel with
made-up percentages. That panel doesn't appear here. Reason: your real
eval harness compares *ungrounded vs grounded* for one provider per run
- it doesn't run both providers simultaneously and compare them. Rather
than build a UI element that implies data the backend doesn't produce,
the dashboard's "per-chart results" section shows what the harness
actually returns: each golden-set chart's ungrounded and grounded rate,
side by side. If a real Groq-vs-Gemini comparison matters later, that's
a small harness extension (run `run_eval()` twice, once per provider),
not a frontend problem.

## Porting Three.js into React: the part that needed care

The original HTML mockup ran Three.js directly against the DOM with
plain `<script>` tags - no cleanup needed, since the whole page reloads
between views. React is different: `Hero3DScene` is a component that can
mount and unmount repeatedly (React's Strict Mode in development
deliberately mounts, unmounts, and remounts every component once, to
surface exactly this class of bug). Without proper cleanup, that would
create a second renderer, a second set of event listeners, and leak
memory on every remount.

The `useEffect` cleanup function handles this: cancels the animation
frame, removes the resize/mousemove listeners, disposes the renderer,
removes its canvas from the DOM, and disposes every mesh's geometry and
material. This is why the component works correctly in Next.js dev mode
(where the double-mount would otherwise be visible as a frozen or
duplicated scene) and not just in a simplified demo.

## `lib/api.ts`: the honesty layer between frontend and backend

Every interface in this file mirrors a real pydantic model from the
backend - `ComputedChart`, `GenerationResult`, `EvalReport` - field for
field. This isn't just type safety for its own sake: it means if a
backend response shape ever changes, TypeScript will flag every place
in the frontend that assumed the old shape, rather than the mismatch
surfacing silently as `undefined` in the rendered page.

## Design choice: eval doesn't auto-run on page load

The dashboard's hero stat starts empty, with a "Run live eval" button,
rather than firing `POST /api/eval/run` automatically when the page
loads. That endpoint makes 10 real LLM API calls per run - fine for a
deliberate click, not something that should fire every time someone
(or a search engine crawler, or a page refresh) loads the dashboard.

## Known gaps, honestly

- No loading skeleton for the "try it yourself" claims list - it's a
  plain "Generating…" button state, functional but not polished
- No error boundary around the 3D scene - if WebGL isn't available
  (extremely old browser, some locked-down environments), the landing
  page's background simply won't render rather than falling back
  gracefully. Worth a fix before treating this as production-grade,
  not urgent for a portfolio piece
- `npm audit` flags a `sharp` (image processing) transitive dependency
  vulnerability inherited from Next.js's image optimization feature.
  This app doesn't use `next/image` anywhere, so that code path isn't
  reachable - documented here rather than silently ignored, in the same
  spirit as every other "known limitation" noted through this project

## Try it on your machine

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Then, with your backend also running (`uvicorn app.main:app --reload`
from `backend/`), open `http://localhost:3000`. Hover the planets on the
landing page, then go to `/dashboard` and click "Run live eval" for the
real numbers.
