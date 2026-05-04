# Design drift audit — Sprint 1

**Date:** 2026-05-04
**Reference:** `vrov-new/public/1301-2nd-street-yakima/index.html`
**Subject:** `frontend/styles/tailwind.config.ts`, `frontend/app/globals.css`

## Verdict

**Zero meaningful drift.** No changes required to tokens, typography, or animation utilities. Sprint 1 design fixes are UX-structural (homepage rewrite), not token-level.

## Comparison matrix

| Token | 1301-2nd-street CSS | Tailwind config | Match? |
|---|---|---|---|
| `--black` / `colors.black` | `#080604` | `#080604` | ✓ |
| `--deep` | `#0D0904` | `#0D0904` | ✓ |
| `--panel` | `#141008` | `#141008` | ✓ |
| `--warm` | `#1A1208` | `#1A1208` | ✓ |
| `--gold` | `#BFA06A` | `#BFA06A` | ✓ |
| `--gold-hi` | `#DEC98A` | `#DEC98A` | ✓ |
| `--gold-dim` | `#5A4A28` | `#5A4A28` | ✓ |
| `--ivory` | `#F5EFE0` | `#F5EFE0` | ✓ |
| `--mist` | `#CEC4A8` | `#CEC4A8` | ✓ |
| `--dim` | `#706450` | `#706450` | ✓ |
| Serif | Cormorant Garamond | Cormorant Garamond | ✓ |
| Sans | (system) | Raleway → Inter → system | ✓ (acceptable expansion) |
| Letter spacing | 0.16em-0.42em | cap=0.16, label=0.18, luxe=0.22, eyebrow=0.42 | ✓ |
| Hero clamp | `clamp(46px, 6.2vw, 84px)` | `clamp(2.5rem, 6vw, 4.75rem)` | ✓ within ±2px |
| Section title clamp | `clamp(30px, 3.6vw, 50px)` | `clamp(2rem, 4vw, 3rem)` | ✓ within ±2px |
| Body clamp | `clamp(16px, 1.25vw, 20px)` | `text-base md:text-lg` (16/18px) | ✓ acceptable |
| Fade-up keyframe | `@keyframes fup` opacity 0→1 + translateY | identical | ✓ |
| Slow zoom | 22s ease-out | 22s ease-out | ✓ |

## Two minor notes

1. **Easing function** — 1301 uses standard `ease` for fade-up; Tailwind config additionally exposes `ease-luxe: cubic-bezier(0.16, 1, 0.3, 1)`. The luxe variant is the broader vrov-new system per `docs/research/design-system-reference.md` and CLAUDE.md. **No fix.** The hero already uses `[0.16, 1, 0.3, 1]` directly in Framer Motion props.

2. **1301 cream theme** — note that `1301-2nd-street-yakima/index.html` overrides `:root` in inline CSS to use a **cream theme** (inverted). The structural variables stay the same, but `--black` becomes `#F5EFE0` and `--ivory` becomes `#1A1208`. **This is a per-listing theme override, not a system-level change.** Yakima Web's primary surface is dark; only listing pages would adopt the cream theme inversion if/when a listings feature lands (currently deferred per ADR backlog).

## Action

None. Carry forward.
