"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { api, EvalReport, PanchangDay } from "@/lib/api";
import CssStarfield from "@/components/CssStarfield";
import HistorySection from "@/components/HistorySection";

// TryItYourselfCard is the sole consumer of framer-motion in this app
// (~111KB parsed, its own chunk) - the expand/collapse animation isn't
// needed for first paint, so deferring it keeps that weight out of the
// dashboard's initial JS. The fallback mirrors the collapsed card's
// structure (same padding, same header row, same input-row shape) so
// there's no layout shift when the real chunk swaps in.
const TryItYourselfCard = dynamic(() => import("@/components/TryItYourselfCard"), {
  loading: () => (
    <div className="glass p-7 animate-pulse">
      <div className="flex items-start justify-between gap-3 mb-1">
        <div className="h-4 w-28 rounded bg-white/10" />
        <div className="w-7 h-7 rounded-full bg-white/5" />
      </div>
      <div className="h-3 w-56 rounded bg-white/5 mb-5 mt-2" />
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="h-10 rounded-xl bg-white/[0.04] border border-white/10" />
        <div className="h-10 rounded-xl bg-white/[0.04] border border-white/10" />
      </div>
      <div className="h-11 rounded-xl bg-white/10" />
    </div>
  ),
});

export default function DashboardPage() {
  const [panchang, setPanchang] = useState<PanchangDay | null>(null);
  const [panchangError, setPanchangError] = useState<string | null>(null);

  const [evalReport, setEvalReport] = useState<EvalReport | null>(null);
  const [evalLoading, setEvalLoading] = useState(false);
  const [evalError, setEvalError] = useState<string | null>(null);

  useEffect(() => {
    api
      .todaysPanchang()
      .then(setPanchang)
      .catch((e) => setPanchangError(e.message));
  }, []);

  async function handleRunEval() {
    setEvalLoading(true);
    setEvalError(null);
    try {
      const report = await api.runEval("groq");
      setEvalReport(report);
    } catch (e: any) {
      setEvalError(e.message ?? "Eval run failed");
    } finally {
      setEvalLoading(false);
    }
  }

  const ungroundedPct = evalReport ? evalReport.avg_ungrounded_hallucination_rate * 100 : null;
  const groundedPct = evalReport ? evalReport.avg_grounded_hallucination_rate * 100 : null;
  const reductionPct = evalReport ? evalReport.relative_reduction * 100 : null;

  return (
    <main className="min-h-screen p-5 sm:p-11 max-w-[1180px] mx-auto">
      <CssStarfield />
      <header className="flex flex-wrap justify-between items-center gap-3 mb-8 sm:mb-10">
        <div>
          <div className="font-serif text-2xl sm:text-3xl font-semibold gold-text">Pramana</div>
          <div className="text-[10px] sm:text-xs uppercase tracking-widest text-indigo mt-0.5">Grounded generation</div>
        </div>
        <nav className="glass flex gap-2 p-1.5 rounded-full">
          <Link href="/" className="px-4 py-2 rounded-full text-sm text-[#b8b4dd] hover:text-white transition-colors">
            Home
          </Link>
          <span className="px-4 py-2 rounded-full text-sm bg-gold/15 text-goldLight">Dashboard</span>
        </nav>
      </header>

      {/* Hero stat */}
      <div className="glass p-5 sm:p-9 mb-6 sm:mb-7 flex justify-between items-center gap-8 flex-wrap">
        <div>
          <div className="text-xs uppercase tracking-widest text-indigo mb-2">
            Measured hallucination rate {evalReport ? `· ${evalReport.provider}` : ""}
          </div>
          {evalReport ? (
            <>
              <div className="text-3xl sm:text-4xl font-mono font-semibold">
                <span className="text-rose">{ungroundedPct?.toFixed(1)}%</span>
                <span className="text-indigoDeep mx-2.5 text-2xl sm:text-3xl">→</span>
                <span className="text-mint">{groundedPct?.toFixed(1)}%</span>
              </div>
              <div className="text-xs text-indigo mt-2.5">
                Ungrounded baseline vs. Pramana-verified generation · {evalReport.cases.length} charts evaluated
              </div>
            </>
          ) : (
            <div className="text-sm text-indigo">
              {evalLoading ? "Running live eval — this makes real API calls, give it a moment…" : "Run a live eval to see real numbers"}
            </div>
          )}
          {evalError && <div className="text-sm text-rose mt-2">{evalError}</div>}
        </div>
        <div className="flex items-center gap-6">
          {reductionPct !== null && (
            <div className="w-27 h-27 rounded-full flex items-center justify-center bg-[conic-gradient(theme(colors.gold)_0deg,theme(colors.gold)_calc(var(--pct)*3.6deg),rgba(255,255,255,0.08)_0deg)]"
                 style={{ ["--pct" as any]: reductionPct }}>
              <div className="w-21 h-21 rounded-full bg-[#0a0a1a] flex flex-col items-center justify-center">
                <b className="text-xl font-mono text-goldLight">{reductionPct.toFixed(0)}%</b>
                <span className="text-[9px] uppercase tracking-wide text-indigo">reduction</span>
              </div>
            </div>
          )}
          <button className="btn-primary" onClick={handleRunEval} disabled={evalLoading}>
            {evalLoading ? "Running…" : evalReport ? "Re-run eval" : "Run live eval"}
          </button>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6 mb-7">
        <TryItYourselfCard />

        {/* Today's fact - genuinely computed, not generated */}
        <div className="glass p-7 flex flex-col gap-3.5">
          <div className="text-2xl text-goldLight">☾</div>
          {panchangError && <div className="text-sm text-rose">{panchangError}</div>}
          {panchang ? (
            <>
              <div className="font-serif text-lg leading-snug text-[#ede9f7]">
                Today's Moon sits in {panchang.nakshatra} nakshatra, with the Sun in {panchang.sun_sign}.
                The tithi is {panchang.tithi}.
              </div>
              <div className="text-[11px] font-mono uppercase tracking-wide text-indigoDeep">
                Computed from today's panchang · not generated
              </div>
            </>
          ) : (
            !panchangError && <div className="text-sm text-indigo">Loading today's panchang…</div>
          )}
        </div>
      </div>

      {/* Per-case eval breakdown */}
      {evalReport && (
        <div className="glass p-7 mb-7">
          <div className="text-[15px] font-medium mb-1">Per-chart results</div>
          <div className="text-xs text-indigo mb-5">Each row is one chart from the golden set, both conditions checked against the same real ground truth</div>
          <div className="space-y-4">
            {evalReport.cases.map((c, i) => (
              <div key={i} className="flex flex-wrap justify-between items-center gap-x-6 gap-y-1.5 py-3 border-b border-white/[0.06] last:border-0">
                <div className="text-[13px] text-[#d4d1ec] font-mono">
                  {c.birth_details.date} · {c.birth_details.time}
                </div>
                <div className="flex gap-6 text-sm font-mono">
                  <span className="text-rose">{(c.ungrounded_result.hallucination_rate * 100).toFixed(0)}% ungrounded</span>
                  <span className="text-mint">{(c.grounded_result.hallucination_rate * 100).toFixed(0)}% grounded</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <HistorySection />
    </main>
  );
}
