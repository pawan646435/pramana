import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pramana — Grounded Generation",
  description:
    "A hallucination-grounded generation system: deterministic computation produces ground truth, an LLM narrates it, and every claim is verified against the source.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
