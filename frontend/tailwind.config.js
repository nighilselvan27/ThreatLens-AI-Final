/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: "#0a0e17",
          surface: "#0f1420",
          elevated: "#131a2a",
        },
        border: {
          DEFAULT: "rgba(148, 163, 184, 0.12)",
        },
        accent: {
          cyan: "#22d3ee",
          blue: "#3b82f6",
          purple: "#a855f7",
          indigo: "#6366f1",
        },
        severity: {
          critical: "#f43f5e",
          high: "#fb923c",
          medium: "#facc15",
          low: "#34d399",
          info: "#38bdf8",
        },
        muted: "#94a3b8",
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        glow: "0 0 24px rgba(34, 211, 238, 0.15)",
        "glow-purple": "0 0 24px rgba(168, 85, 247, 0.18)",
        card: "0 4px 24px rgba(0,0,0,0.35)",
      },
      backgroundImage: {
        "grid-pattern":
          "linear-gradient(rgba(148,163,184,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.05) 1px, transparent 1px)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        scan: "scan 2.5s linear infinite",
      },
      keyframes: {
        scan: {
          "0%": { transform: "translateY(-100%)" },
          "100%": { transform: "translateY(100%)" },
        },
      },
    },
  },
  plugins: [],
};
