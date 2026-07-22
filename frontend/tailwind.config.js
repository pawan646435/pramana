/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        void: "#05060f",
        panel: "rgba(255,255,255,0.05)",
        gold: "#c9a86a",
        goldLight: "#f0dca0",
        indigo: "#8b87c2",
        indigoDeep: "#6f6bb0",
        rose: "#d4787a",
        mint: "#6fd4a8",
      },
      fontFamily: {
        serif: ["Cormorant Garamond", "serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
