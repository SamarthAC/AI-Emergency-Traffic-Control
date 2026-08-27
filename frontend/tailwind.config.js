/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#0B1220",
        surface: "#111827",
        "surface-hover": "#161F2E",
        border: "#1F2A3C",
        primary: {
          DEFAULT: "#00E5FF",
          dim: "#0AA8BD",
        },
        emergency: {
          DEFAULT: "#FF3B30",
          dim: "#7A1D18",
        },
        signal: {
          green: "#00C853",
          orange: "#FF9800",
          red: "#FF3B30",
        },
        muted: "#8291A8",
        "text-primary": "#E6EDF5",
      },
      fontFamily: {
        display: ["'Rajdhani'", "'Sora'", "sans-serif"],
        body: ["'Sora'", "'Inter'", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
      },
      boxShadow: {
        panel: "0 4px 24px rgba(0,0,0,0.45)",
        glow: "0 0 12px rgba(0,229,255,0.55)",
        "glow-red": "0 0 14px rgba(255,59,48,0.7)",
        "glow-green": "0 0 12px rgba(0,200,83,0.65)",
      },
      animation: {
        "pulse-slow": "pulse 2.4s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "spin-slow": "spin 3s linear infinite",
      },
      backgroundImage: {
        "grid-fade":
          "radial-gradient(circle at 1px 1px, rgba(0,229,255,0.08) 1px, transparent 0)",
      },
    },
  },
  plugins: [],
};
