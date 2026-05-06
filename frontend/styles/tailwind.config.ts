import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx,js,jsx}",
    "./components/**/*.{ts,tsx,js,jsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Cream palette (Option C — vrov-new 1301 inversion)
        black: "#F5EFE0",
        deep: "#EDE5CD",
        panel: "#E5DBBC",
        warm: "#D8C9A4",
        gold: "#8B7340",
        "gold-hi": "#B89860",
        "gold-dim": "#5A4A28",
        ivory: "#1A1208",
        mist: "#5A4F42",
        dim: "#4A3F2A",
        // Dark counterweights (footer, dark overlays, dark CTAs, scrolled nav)
        "dark-bg": "#080604",
        "dark-deep": "#0D0904",
        "dark-panel": "#141008",
        "dark-warm": "#1A1208",
        "dark-text": "#F5EFE0",
        "dark-mist": "#CEC4A8",
        "dark-dim": "#706450",
        // Status pips — adjusted for cream contrast
        ok: "#3F8A4E",
        warn: "#A87420",
        err: "#B23A3A",
      },
      fontFamily: {
        serif: ['"Cormorant Garamond"', "Georgia", "serif"],
        sans: [
          "Raleway",
          "Inter",
          "system-ui",
          "-apple-system",
          "sans-serif",
        ],
      },
      letterSpacing: {
        luxe: "0.22em",
        eyebrow: "0.42em",
        label: "0.18em",
        cap: "0.16em",
      },
      borderRadius: {
        xs: "calc(var(--radius) - 6px)",
        sm: "calc(var(--radius) - 4px)",
        md: "calc(var(--radius) - 2px)",
        lg: "var(--radius)",
        xl: "calc(var(--radius) + 4px)",
        "2xl": "calc(var(--radius) + 8px)",
      },
      boxShadow: {
        card: "0 4px 6px -1px rgba(0,0,0,0.18), 0 2px 4px -2px rgba(0,0,0,0.12)",
        "card-hover":
          "0 20px 25px -5px rgba(0,0,0,0.35), 0 8px 10px -6px rgba(0,0,0,0.22)",
        hero: "0 25px 50px -12px rgba(0,0,0,0.5)",
        "gold-glow": "0 0 24px -6px rgba(191,160,106,0.45)",
      },
      transitionTimingFunction: {
        luxe: "cubic-bezier(0.16, 1, 0.3, 1)",
      },
      keyframes: {
        fup: {
          "0%": { opacity: "0", transform: "translateY(26px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        zoomout: {
          "0%": { transform: "scale(1.05)" },
          "100%": { transform: "scale(1)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        fadein: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        fadeinup: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-up": "fup 1s 0.3s ease both",
        "fade-up-1": "fup 1s 0.4s ease both",
        "fade-up-2": "fup 1s 0.55s ease both",
        "fade-up-3": "fup 1s 0.7s ease both",
        "slow-zoom": "zoomout 22s ease-out forwards",
        shimmer: "shimmer 3s linear infinite",
        "fade-in": "fadein 600ms ease both",
        "fade-in-up": "fadeinup 700ms ease both",
      },
      maxWidth: {
        "8xl": "88rem",
      },
      opacity: {
        14: "0.14",
        22: "0.22",
        35: "0.35",
        52: "0.52",
        85: "0.85",
      },
    },
  },
  plugins: [],
};

export default config;
