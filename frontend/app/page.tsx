"use client";

import Link from "next/link";
import dynamic from "next/dynamic";
import { useIsCoarsePointer } from "@/lib/useIsCoarsePointer";

// Three.js + procedural texture generation is the single heaviest chunk
// in this app. It needs a real DOM/WebGL context (can't run server-side
// anyway), so ssr:false is free - no hydration cost avoided, just load
// deferred until the browser actually needs it. The fallback is a plain
// gradient matching the page background, not a scene skeleton, so there's
// no layout shift and nothing to visually "swap out" once the real chunk
// mounts - it just fades in on top of an already-correct-looking backdrop.
const Hero3DScene = dynamic(() => import("@/components/Hero3DScene"), {
  ssr: false,
  loading: () => (
    <div
      className="fixed inset-0 z-0 animate-pulse"
      style={{ background: "radial-gradient(ellipse at 30% 10%, #12122b 0%, #05060f 55%, #030308 100%)" }}
    />
  ),
});

export default function LandingPage() {
  const isCoarsePointer = useIsCoarsePointer();
  // cursor-none only makes sense where the custom star cursor replaces
  // the system cursor (mouse/trackpad) - there's no cursor to hide on touch.
  const cursorClass = isCoarsePointer ? "" : "cursor-none";

  return (
    <main className={`relative min-h-[170vh] select-none ${cursorClass}`}>
      <Hero3DScene />

      {/* Header stays pinned at the very top regardless of scroll - the
          scene behind it is also fixed, so this always reads as "on top
          of the sky", never competing with the hero copy below. */}
      <header className="fixed top-0 inset-x-0 z-20 flex flex-wrap justify-between items-start gap-3 px-5 py-6 sm:px-11 sm:py-10">
        <div>
          <div className="font-serif text-2xl sm:text-3xl font-semibold">Pramana</div>
          <div className="text-[10px] sm:text-xs uppercase tracking-widest text-indigo mt-1">Grounded generation</div>
        </div>
        <div className="flex flex-col items-end gap-3">
          <nav className="glass flex gap-1 sm:gap-2 p-1.5 rounded-full">
            <span className="px-3 sm:px-4 py-2 rounded-full text-sm bg-gold/15 text-goldLight">Home</span>
            <Link href="/dashboard" className={`px-3 sm:px-4 py-2 rounded-full text-sm text-[#b8b4dd] hover:text-white transition-colors ${cursorClass}`}>
              Dashboard
            </Link>
          </nav>
          {/* On very narrow screens this hint pill competes for space with
              the logo, so it's hidden below 400px - the drag/tap gestures
              are discoverable enough without it once the screen is that tight. */}
          <div className="hidden min-[400px]:block glass px-4 py-2 rounded-full text-[11px] text-indigo max-w-[80vw] sm:max-w-none">
            <b className="text-goldLight font-medium">Drag</b> a planet along its orbit ·{" "}
            {isCoarsePointer ? (
              <>
                <b className="text-goldLight font-medium">Tap</b> for a grounded fact
              </>
            ) : (
              <>
                <b className="text-goldLight font-medium">Hover</b> for a grounded fact
              </>
            )}
          </div>
        </div>
      </header>

      {/* Hero copy sits well below the first fold, in its own clear
          space beneath the solar system's visual footprint, with a
          scrim behind it for legibility over the starfield. */}
      <div className="relative z-10 flex justify-center pt-[100vh] pb-32 px-5 sm:px-11">
        <div
          className="max-w-[560px] w-full rounded-3xl p-6 sm:p-10"
          style={{ background: "radial-gradient(ellipse at center, rgba(3,3,8,0.7) 0%, rgba(3,3,8,0.3) 70%, rgba(3,3,8,0) 100%)" }}
        >
          <div className="text-xs uppercase tracking-widest text-indigo mb-4 text-center">A valid means of knowledge</div>
          <h1 className="font-serif text-3xl sm:text-4xl md:text-5xl font-semibold leading-[1.15] mb-6 text-center">
            Every claim, <span className="gold-text">traced to its source</span>
          </h1>
          <p className="text-[15px] text-[#b8b4dd] leading-relaxed mb-8 text-center">
            Pramana pairs deterministic astronomical computation with LLM narration — every
            generated statement is verified against real, computed planetary data, not invented.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/dashboard" className={`btn-primary block sm:inline-block text-center ${cursorClass}`}>
              Generate your chart
            </Link>
            <Link href="/dashboard" className={`btn-secondary block sm:inline-block text-center ${cursorClass}`}>
              View grounding dashboard
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
