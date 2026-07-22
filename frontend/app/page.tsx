import Link from "next/link";
import Hero3DScene from "@/components/Hero3DScene";

export default function LandingPage() {
  return (
    <main className="relative min-h-[170vh] cursor-none select-none">
      <Hero3DScene />

      {/* Header stays pinned at the very top regardless of scroll - the
          scene behind it is also fixed, so this always reads as "on top
          of the sky", never competing with the hero copy below. */}
      <header className="fixed top-0 inset-x-0 z-20 flex justify-between items-start px-11 py-10">
        <div>
          <div className="font-serif text-3xl font-semibold">Pramana</div>
          <div className="text-xs uppercase tracking-widest text-indigo mt-1">Grounded generation</div>
        </div>
        <div className="flex flex-col items-end gap-3">
          <nav className="glass flex gap-2 p-1.5 rounded-full">
            <span className="px-4 py-2 rounded-full text-sm bg-gold/15 text-goldLight">Home</span>
            <Link href="/dashboard" className="px-4 py-2 rounded-full text-sm text-[#b8b4dd] hover:text-white transition-colors cursor-none">
              Dashboard
            </Link>
          </nav>
          <div className="glass px-4 py-2 rounded-full text-[11px] text-indigo">
            <b className="text-goldLight font-medium">Drag</b> a planet along its orbit ·{" "}
            <b className="text-goldLight font-medium">Hover</b> for a grounded fact
          </div>
        </div>
      </header>

      {/* Hero copy sits well below the first fold, in its own clear
          space beneath the solar system's visual footprint, with a
          scrim behind it for legibility over the starfield. */}
      <div className="relative z-10 flex justify-center pt-[100vh] pb-32 px-11">
        <div
          className="max-w-[560px] rounded-3xl p-10"
          style={{ background: "radial-gradient(ellipse at center, rgba(3,3,8,0.7) 0%, rgba(3,3,8,0.3) 70%, rgba(3,3,8,0) 100%)" }}
        >
          <div className="text-xs uppercase tracking-widest text-indigo mb-4 text-center">A valid means of knowledge</div>
          <h1 className="font-serif text-5xl font-semibold leading-[1.15] mb-6 text-center">
            Every claim, <span className="gold-text">traced to its source</span>
          </h1>
          <p className="text-[15px] text-[#b8b4dd] leading-relaxed mb-8 text-center">
            Pramana pairs deterministic astronomical computation with LLM narration — every
            generated statement is verified against real, computed planetary data, not invented.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/dashboard" className="btn-primary inline-block cursor-none">
              Generate your chart
            </Link>
            <Link href="/dashboard" className="btn-secondary inline-block cursor-none">
              View grounding dashboard
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
