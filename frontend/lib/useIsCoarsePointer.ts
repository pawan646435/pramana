"use client";

import { useEffect, useState } from "react";

/**
 * True on touch/stylus-primary devices (no reliable hover, coarse
 * pointer resolution), false on mouse/trackpad. Starts false (matches
 * desktop, and matches SSR output) and flips after mount once
 * `matchMedia` is available - never trust this value during the first
 * render, only after the effect runs.
 */
export function useIsCoarsePointer(): boolean {
  const [isCoarse, setIsCoarse] = useState(false);

  useEffect(() => {
    const mql = window.matchMedia("(pointer: coarse)");
    setIsCoarse(mql.matches);

    function onChange(e: MediaQueryListEvent) {
      setIsCoarse(e.matches);
    }
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return isCoarse;
}
