/** @type {import('tailwindcss').Config} */
// Tokens ported from C:\Users\vladi\OneDrive\Desktop\Projects\vrov-new\tailwind.config.ts
// See docs/research/design-system-reference.md for full audit + rationale.

export default {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
    "./static/src/js/**/*.js",
    "./static/src/react/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        black: "#080604",
        deep: "#0D0904",
        panel: "#141008",
        warm: "#1A1208",
        gold: "#BFA06A",
        "gold-hi": "#DEC98A",
        "gold-dim": "#5A4A28",
        ivory: "#F5EFE0",
        mist: "#CEC4A8",
        dim: "#706450",
        // Status accents (sparingly)
        ok: "#65A05B",
        warn: "#D4A446",
        err: "#C66B5C",
      },
      fontFamily: {
        serif: ['"Cormorant Garamond"', 'Georgia', 'serif'],
        sans:  ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      letterSpacing: {
        luxe: "0.22em",
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
        "card-hover": "0 20px 25px -5px rgba(0,0,0,0.35), 0 8px 10px -6px rgba(0,0,0,0.22)",
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
      },
      animation: {
        "fade-up": "fup 1s 0.3s ease both",
        "slow-zoom": "zoomout 22s ease-out forwards",
        "shimmer": "shimmer 3s linear infinite",
      },
      maxWidth: {
        "8xl": "88rem",
      },
      opacity: {
        14: "0.14",
        22: "0.22",
        35: "0.35",
        85: "0.85",
      },
    },
  },
  plugins: [
    require("@tailwindcss/forms")({ strategy: "class" }),
    require("@tailwindcss/typography"),
    require("tailwindcss-animate"),
  ],
};
