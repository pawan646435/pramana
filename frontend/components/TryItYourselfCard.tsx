"use client";

import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { AnimatePresence, motion } from "framer-motion";
import { api, ClaimStatus, GenerationResult } from "@/lib/api";
import ErrorNotice from "@/components/ErrorNotice";

const STATUS_STYLES: Record<ClaimStatus, { badge: string; icon: string }> = {
  grounded: { badge: "badge-grounded", icon: "✓" },
  ungrounded: { badge: "badge-ungrounded", icon: "!" },
  unverifiable: { badge: "badge-unverifiable", icon: "?" },
};

function ExpandIcon({ expanded }: { expanded: boolean }) {
  // A single glyph that toggles between "point outward" (expand) and
  // "point inward" (collapse) rather than two separate icons.
  return (
    <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
      {expanded ? (
        <path
          d="M6 2v3a1 1 0 0 1-1 1H2M9 2v3a1 1 0 0 0 1 1h3M6 13v-3a1 1 0 0 0-1-1H2M9 13v-3a1 1 0 0 1 1-1h3"
          stroke="currentColor"
          strokeWidth="1.3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ) : (
        <path
          d="M2 5V2h3M10 2h3v3M13 10v3h-3M5 13H2v-3"
          stroke="currentColor"
          strokeWidth="1.3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      )}
    </svg>
  );
}

interface NarrativeProps {
  result: GenerationResult;
  expanded: boolean;
}

function Narrative({ result, expanded }: NarrativeProps) {
  return (
    <div className={expanded ? "mt-4" : "mt-4 pt-4 border-t border-white/10"}>
      <div className={`font-serif text-[#ede9f7] leading-relaxed ${expanded ? "text-xl" : "text-lg"}`}>
        {result.narrative}
      </div>
    </div>
  );
}

interface ClaimsListProps {
  result: GenerationResult;
  scrollable: boolean;
}

function ClaimsList({ result, scrollable }: ClaimsListProps) {
  return (
    <div className="mt-5 pt-4 border-t border-white/10">
      <div className="text-xs text-indigo mb-3">
        How this was verified · Hallucination rate: <span className="text-goldLight font-mono">{(result.hallucination_rate * 100).toFixed(0)}%</span>
        {" · "}
        {result.model_used}
      </div>
      <div className={`space-y-3 ${scrollable ? "max-h-80 overflow-y-auto" : ""}`}>
        {result.claims.map((c, i) => {
          const style = STATUS_STYLES[c.status];
          return (
            <div key={i} className="flex gap-3">
              <div className={`w-5.5 h-5.5 rounded-full flex items-center justify-center text-xs shrink-0 ${style.badge}`}>
                {style.icon}
              </div>
              <div>
                <div className="text-[13.5px] text-[#d4d1ec] leading-snug">{c.claim.text}</div>
                {c.grounded_field_path && (
                  <div className="text-[11px] font-mono text-indigoDeep mt-0.5">→ {c.grounded_field_path}</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

interface CardBodyProps {
  expanded: boolean;
  onToggleExpand: () => void;
  tryBirth: { date: string; time: string };
  setTryBirth: (b: { date: string; time: string; latitude: number; longitude: number; timezone_offset_hours: number }) => void;
  tryLoading: boolean;
  tryError: string | null;
  tryResult: GenerationResult | null;
  onGenerate: () => void;
  fullBirth: { date: string; time: string; latitude: number; longitude: number; timezone_offset_hours: number };
}

function CardBody({
  expanded,
  onToggleExpand,
  tryLoading,
  tryError,
  tryResult,
  onGenerate,
  fullBirth,
  setTryBirth,
}: CardBodyProps) {
  return (
    <>
      <div className="flex items-start justify-between gap-3 mb-1">
        <div className="text-[15px] font-medium">Try it yourself</div>
        <button
          onClick={onToggleExpand}
          aria-label={expanded ? "Collapse card" : "Expand card"}
          className="shrink-0 -m-2.5 w-11 h-11 rounded-full flex items-center justify-center text-indigo hover:text-goldLight hover:bg-white/[0.06] focus:outline-none focus:ring-1 focus:ring-gold/40 transition-colors"
        >
          <ExpandIcon expanded={expanded} />
        </button>
      </div>
      <div className="text-xs text-indigo mb-5">Enter birth details for a live, verified reading</div>

      <div className="grid grid-cols-2 gap-3 mb-4">
        <input
          type="date"
          value={fullBirth.date}
          onChange={(e) => setTryBirth({ ...fullBirth, date: e.target.value })}
          className="bg-white/[0.04] border border-white/10 rounded-xl px-3 py-2.5 text-sm"
        />
        <input
          type="time"
          value={fullBirth.time}
          onChange={(e) => setTryBirth({ ...fullBirth, time: e.target.value })}
          className="bg-white/[0.04] border border-white/10 rounded-xl px-3 py-2.5 text-sm"
        />
      </div>
      <button className="btn-primary w-full mb-4" onClick={onGenerate} disabled={tryLoading}>
        {tryLoading ? "Generating…" : "Generate reading"}
      </button>
      {tryError && <ErrorNotice message={tryError} className="mb-3" />}

      {tryLoading && !tryResult && (
        <div className="mt-4 pt-4 border-t border-white/10 space-y-3 animate-pulse" aria-label="Generating reading">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="flex gap-3">
              <div className="w-5.5 h-5.5 rounded-full bg-white/10 shrink-0" />
              <div className="flex-1 space-y-1.5 pt-0.5">
                <div className="h-2.5 rounded-full bg-white/10" style={{ width: `${85 - i * 12}%` }} />
                <div className="h-2.5 rounded-full bg-white/[0.06]" style={{ width: `${55 - i * 8}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}

      {tryResult && (
        <>
          <Narrative result={tryResult} expanded={expanded} />
          <ClaimsList result={tryResult} scrollable={!expanded} />
        </>
      )}
    </>
  );
}

export default function TryItYourselfCard() {
  const [tryBirth, setTryBirth] = useState({
    date: "1998-04-12",
    time: "14:35",
    latitude: 25.59,
    longitude: 85.13,
    timezone_offset_hours: 5.5,
  });
  const [tryResult, setTryResult] = useState<GenerationResult | null>(null);
  const [tryLoading, setTryLoading] = useState(false);
  const [tryError, setTryError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    if (!expanded) return;
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setExpanded(false);
    }
    window.addEventListener("keydown", onKeyDown);
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = "";
    };
  }, [expanded]);

  async function handleTryIt() {
    setTryLoading(true);
    setTryError(null);
    setTryResult(null);
    try {
      const result = await api.generateNarrative(tryBirth, "groq");
      setTryResult(result);
    } catch (e: any) {
      setTryError(e.message ?? "Generation failed");
    } finally {
      setTryLoading(false);
    }
  }

  const bodyProps = {
    tryBirth,
    setTryBirth,
    tryLoading,
    tryError,
    tryResult,
    onGenerate: handleTryIt,
    fullBirth: tryBirth,
  };

  return (
    <>
      {/* Collapsed, in-flow card. When expanded, this slot renders an
          invisible placeholder of the same size so the grid layout
          doesn't reflow, while the real content lives in the portal
          below sharing the same layoutId - Framer Motion animates the
          bounding box between the two automatically. */}
      <motion.div layoutId="try-it-card" className="glass p-7" style={{ visibility: expanded ? "hidden" : "visible" }}>
        {!expanded && (
          <CardBody expanded={false} onToggleExpand={() => setExpanded(true)} {...bodyProps} />
        )}
      </motion.div>

      {mounted &&
        createPortal(
          <AnimatePresence>
            {expanded && (
              <>
                <motion.div
                  key="backdrop"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="fixed inset-0 bg-black/70 z-40"
                  onClick={() => setExpanded(false)}
                  aria-hidden="true"
                />
                {/* Edge-to-edge on small viewports (90vw is still cramped
                    with wasted margin on a phone) - only becomes a
                    floating centered card with real margin from sm: up. */}
                <div className="fixed inset-0 z-50 flex items-center justify-center p-0 sm:p-6 pointer-events-none">
                  <motion.div
                    layoutId="try-it-card"
                    className="glass p-5 sm:p-9 fixed inset-4 sm:static sm:w-[85vw] sm:max-w-[900px] sm:h-[75vh] overflow-y-auto pointer-events-auto"
                    role="dialog"
                    aria-modal="true"
                    aria-label="Try it yourself - expanded"
                  >
                    <CardBody expanded={true} onToggleExpand={() => setExpanded(false)} {...bodyProps} />
                  </motion.div>
                </div>
              </>
            )}
          </AnimatePresence>,
          document.body
        )}
    </>
  );
}
