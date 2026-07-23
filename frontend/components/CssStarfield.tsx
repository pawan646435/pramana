"use client";

import { useEffect, useState } from "react";

interface Star {
  top: number;
  left: number;
  size: number;
  delay: number;
  duration: number;
  opacity: number;
}

function generateStars(count: number): Star[] {
  return Array.from({ length: count }, () => ({
    top: Math.random() * 100,
    left: Math.random() * 100,
    size: Math.random() * 1.6 + 0.6,
    delay: Math.random() * 6,
    duration: Math.random() * 3 + 3,
    opacity: Math.random() * 0.5 + 0.25,
  }));
}

/**
 * Ambient background texture for data-dense pages - same celestial
 * language as the landing page's Three.js starfield, but plain CSS/DOM
 * so it doesn't add WebGL render cost next to live-updating dashboard
 * content.
 *
 * Star positions are randomized, so they're generated client-side only
 * (after mount) rather than during render - doing it during render would
 * produce a different random layout on the server vs. the client and
 * trip a hydration mismatch.
 */
export default function CssStarfield({ count = 80 }: { count?: number }) {
  const [stars, setStars] = useState<Star[]>([]);

  useEffect(() => {
    setStars(generateStars(count));
  }, [count]);

  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none" aria-hidden="true">
      {stars.map((star, i) => (
        <span
          key={i}
          className="css-star"
          style={{
            top: `${star.top}%`,
            left: `${star.left}%`,
            width: `${star.size}px`,
            height: `${star.size}px`,
            animationDelay: `${star.delay}s`,
            animationDuration: `${star.duration}s`,
            ["--star-opacity" as any]: star.opacity,
          }}
        />
      ))}
    </div>
  );
}
