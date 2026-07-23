"use client";

import { useEffect, useState } from "react";
import { api, EvalRunDetail, EvalRunSummary, GenerationLogSummary } from "@/lib/api";

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function EmptyState({ message }: { message: string }) {
  return (
    <div className="glass px-6 py-8 text-center text-sm text-indigo">
      {message}
    </div>
  );
}

function EvalRunRow({
  run,
  isExpanded,
  onToggle,
}: {
  run: EvalRunSummary;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      className="w-full flex flex-wrap justify-between items-center gap-x-4 gap-y-1.5 py-3 px-3 -mx-3 rounded-xl border-b border-white/[0.06] last:border-0 text-left hover:bg-white/[0.04] focus:outline-none focus:ring-1 focus:ring-gold/40 transition-colors"
      aria-expanded={isExpanded}
    >
      <div className="flex flex-col">
        <span className="text-[13px] text-[#d4d1ec] font-mono">{formatDateTime(run.created_at)}</span>
        <span className="text-[11px] text-indigo uppercase tracking-wide">
          {run.provider} · {run.num_cases} charts
        </span>
      </div>
      <div className="flex gap-3 sm:gap-5 text-sm font-mono items-center">
        <span className="text-rose">{(run.avg_ungrounded_hallucination_rate * 100).toFixed(0)}%</span>
        <span className="text-indigoDeep">→</span>
        <span className="text-mint">{(run.avg_grounded_hallucination_rate * 100).toFixed(0)}%</span>
        <span className="text-goldLight w-10 sm:w-12 text-right">{(run.relative_reduction * 100).toFixed(0)}%</span>
        <span className={`text-indigo transition-transform ${isExpanded ? "rotate-180" : ""}`}>⌄</span>
      </div>
    </button>
  );
}

function EvalRunExpanded({ id }: { id: string }) {
  const [detail, setDetail] = useState<EvalRunDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setDetail(null);
    setError(null);
    api
      .getEvalRun(id)
      .then((d) => !cancelled && setDetail(d))
      .catch((e) => !cancelled && setError(e.message ?? "Failed to load run detail"));
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (error) return <div className="text-sm text-rose py-3 px-3">{error}</div>;
  if (!detail) return <div className="text-sm text-indigo py-3 px-3">Loading case detail…</div>;

  return (
    <div className="py-3 px-3 space-y-3">
      {detail.cases.map((c) => (
        <div key={c.id} className="flex flex-wrap justify-between items-center gap-x-5 gap-y-1 py-2.5 border-b border-white/[0.05] last:border-0">
          <div className="text-[12.5px] text-[#c4c0e0] font-mono">
            {c.birth_date} · {c.birth_time}
          </div>
          <div className="flex gap-5 text-[13px] font-mono">
            <span className="text-rose">{(c.ungrounded_hallucination_rate * 100).toFixed(0)}% ungrounded</span>
            <span className="text-mint">{(c.grounded_hallucination_rate * 100).toFixed(0)}% grounded</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function GenerationRow({ log }: { log: GenerationLogSummary }) {
  const preview = log.narrative.length > 140 ? `${log.narrative.slice(0, 140)}…` : log.narrative;
  return (
    <div className="py-3.5 border-b border-white/[0.06] last:border-0">
      <div className="flex flex-wrap justify-between items-center gap-x-4 gap-y-1 mb-1.5">
        <span className="text-[13px] text-[#d4d1ec] font-mono">
          {log.birth_date} · {log.birth_time}
        </span>
        <div className="flex gap-4 items-center text-[12px] font-mono shrink-0">
          <span className="text-indigo uppercase tracking-wide">{log.provider}</span>
          <span className="text-goldLight">{(log.hallucination_rate * 100).toFixed(0)}% hallucination</span>
        </div>
      </div>
      <div className="text-[12.5px] text-[#a8a4cc] leading-snug">{preview}</div>
    </div>
  );
}

export default function HistorySection() {
  const [runs, setRuns] = useState<EvalRunSummary[] | null>(null);
  const [runsError, setRunsError] = useState<string | null>(null);
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);

  const [generations, setGenerations] = useState<GenerationLogSummary[] | null>(null);
  const [generationsError, setGenerationsError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listEvalRuns(20)
      .then(setRuns)
      .catch((e) => setRunsError(e.message ?? "Failed to load eval run history"));

    api
      .listGenerations(20)
      .then(setGenerations)
      .catch((e) => setGenerationsError(e.message ?? "Failed to load generation history"));
  }, []);

  return (
    <div className="grid md:grid-cols-2 gap-6 mb-7">
      <div className="glass p-7">
        <div className="text-[15px] font-medium mb-1">Past eval runs</div>
        <div className="text-xs text-indigo mb-5">Every recorded run, most recent first — expand a row for its per-chart detail</div>

        {runsError && <div className="text-sm text-rose">{runsError}</div>}
        {!runsError && runs === null && <div className="text-sm text-indigo">Loading eval history…</div>}
        {!runsError && runs !== null && runs.length === 0 && (
          <EmptyState message="No eval runs yet — click “Run live eval” above to create your first one." />
        )}
        {!runsError && runs !== null && runs.length > 0 && (
          <div>
            {runs.map((run) => {
              const isExpanded = expandedRunId === run.id;
              return (
                <div key={run.id}>
                  <EvalRunRow
                    run={run}
                    isExpanded={isExpanded}
                    onToggle={() => setExpandedRunId(isExpanded ? null : run.id)}
                  />
                  {isExpanded && <EvalRunExpanded id={run.id} />}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="glass p-7">
        <div className="text-[15px] font-medium mb-1">Past generations</div>
        <div className="text-xs text-indigo mb-5">Every "try it yourself" call, most recent first</div>

        {generationsError && <div className="text-sm text-rose">{generationsError}</div>}
        {!generationsError && generations === null && <div className="text-sm text-indigo">Loading generation history…</div>}
        {!generationsError && generations !== null && generations.length === 0 && (
          <EmptyState message="No generations yet — use “Try it yourself” to create your first one." />
        )}
        {!generationsError && generations !== null && generations.length > 0 && (
          <div className="max-h-[420px] overflow-y-auto pr-1">
            {generations.map((log) => (
              <GenerationRow key={log.id} log={log} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
