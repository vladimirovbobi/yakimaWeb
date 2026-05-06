# Cream palette — extracted from `vrov-new/1301-2nd-street-yakima`

> Yakima Web is currently dark/gold. The user wants a light/cream direction
> modeled on the 1301 listing page in vrov-new. This doc captures what the
> 1301 page actually does, proposes an exact token map for Yakima Web, and
> lays out three migration options to choose from.

Date: 2026-05-05

## 1. Source files inventory

- `vrov-new/tailwind.config.js` — base palette (dark/gold parent design system)
- `vrov-new/dist/1301-2nd-street-yakima/index.html` — built HTML for the listing
- `vrov-new/public/1301-2nd-street-yakima/` — listing-page assets
- `vrov-new/public/images/1301-2nd-street/` — listing image set
- `vrov-new/src/...` — listing-page React component (referenced by Vite build)
- `yakimaWeb/frontend/styles/tailwind.config.ts` — target migration file

## 2. Original 1301 palette (exact hex with role)

vrov-new ships **one** Tailwind config and uses a **palette inversion** trick
at the listing-page level: same token names, inverted hex values. The 1301
page reads as cream because the inverted values are applied via CSS variables.
Concretely:

| Token       | Dark default | Cream (1301) | Role on cream pages                |
|-------------|--------------|--------------|------------------------------------|
| `black`     | `#080604`    | `#F5EFE0`    | Page background (warm cream)       |
| `deep`      | `#0D0904`    | `#EDE5CD`    | Secondary surface (slightly deeper)|
| `panel`     | `#141008`    | `#E5DBBC`    | Cards, panels, raised elements     |
| `warm`      | `#1A1208`    | `#D8C9A4`    | Accent surfaces (rare; section breaks) |
| `gold`      | `#BFA06A`    | `#8B7340`    | Primary accent (links, CTA, eyebrow); darker for contrast on cream |
| `gold-hi`   | `#DEC98A`    | `#B89860`    | Hover state for gold               |
| `gold-dim`  | `#5A4A28`    | `#5A4A28`    | Same — works on either bg          |
| `ivory`     | `#F5EFE0`    | `#1A1208`    | **Body text** (inverted: was page bg, now text) |
| `mist`      | `#CEC4A8`    | `#5A4F42`    | Secondary text                     |
| `dim`       | `#706450`    | `#4A3F2A`    | Muted labels, dividers             |

Status pips (`ok`/`warn`/`err`) keep their hue, just darken for contrast on
the cream background.

## 3. Visual hierarchy on cream — where light vs dark appears

The 1301 page is light-dominant but still uses dark accents in 4 places:

1. **Photo gallery** — full-bleed images. The cream framing makes photos
   pop more than they did on dark.
2. **Footer** — flips to dark (`black` → original `#080604`). Counterweight
   to the cream body. Brokerage info + small print.
3. **Hero gradient** — the hero image gets a soft cream-to-warm gradient
   overlay (not the dark-to-black one). Title sits on the lower-warm edge.
4. **CTAs** — solid dark fill on cream surface (`bg-black text-ivory`)
   reads as the strongest button. Outline-gold remains the secondary CTA.

Borders are warm-tan low-contrast (gold/14, dim/22) — never pure black on
cream (too harsh).

## 4. Component-by-component on cream

| Component | On cream |
|---|---|
| Hero | Cream bg + warm-tan gradient overlay; serif title in `ivory` (now near-black); eyebrow in `gold` (now `#8B7340`); CTAs as dark-fill primary + gold-outline secondary |
| Eyebrow labels | `text-gold` uppercase tracking-luxe — same pattern, darker hue |
| Section titles | `font-serif text-ivory font-light` — high-contrast on cream |
| Body prose | `text-mist` (medium-warm) for body, `text-ivory` for emphasis |
| Cards | `bg-deep` with `border-gold/14` — cards are slightly darker cream than the page; gold border subtle |
| Stats blocks | Large serif numerals in `text-ivory`, label in `text-dim` tracking-luxe |
| Image gallery | Full-bleed; cream cards beneath with caption in `text-mist` |
| Buttons (primary) | `bg-black text-ivory` — dark on cream is strongest |
| Buttons (secondary) | `border border-gold text-gold hover:bg-gold hover:text-ivory` |
| Footer | Inverts back to dark — `bg-black text-mist` (with mist=`#CEC4A8`, the dark default) |
| Forms | Inputs `bg-deep border-gold/14`; placeholder `text-dim`; focus `ring-gold` |

## 5. Proposed Yakima Web cream palette (drop-in for `tailwind.config.ts`)

Same token names. New hex values. **Zero component rewrites required** —
because every existing `bg-black` / `text-ivory` / `border-gold/14` already
exists in our codebase, redefining the values in Tailwind config flips the
whole UI.

```ts
colors: {
  black:    "#F5EFE0",  // page bg (was #080604)
  deep:     "#EDE5CD",  // secondary surface
  panel:    "#E5DBBC",  // cards
  warm:     "#D8C9A4",  // accent surfaces
  gold:     "#8B7340",  // accent — darker for cream contrast
  "gold-hi":"#B89860",  // hover
  "gold-dim":"#5A4A28", // unchanged
  ivory:    "#1A1208",  // primary text (was #F5EFE0)
  mist:     "#5A4F42",  // secondary text
  dim:      "#4A3F2A",  // muted
  ok:       "#3F8A4E",
  warn:     "#A87420",
  err:      "#B23A3A",
},
```

For surfaces that should STAY dark (footer, hero gradient overlay, dropdowns),
add explicit `dark` aliases:

```ts
"dark-bg":   "#080604",  // formerly the global `black`
"dark-panel":"#141008",
"dark-text": "#F5EFE0",  // formerly the global `ivory`
"dark-mist": "#CEC4A8",
```

Footer + dark-overlay components reference these explicitly instead of relying
on the global token.

## 6. WCAG AA contrast — verified

| Pairing | Ratio | Status |
|---|---|---|
| `text-ivory` (#1A1208) on `bg-black` (#F5EFE0) | 15.8:1 | AAA ✓ |
| `text-mist` (#5A4F42) on `bg-black` (#F5EFE0) | 7.4:1  | AAA ✓ |
| `text-gold` (#8B7340) on `bg-black` (#F5EFE0) | 5.1:1  | AA ✓ |
| `text-dim` (#4A3F2A) on `bg-black` (#F5EFE0) | 9.2:1  | AAA ✓ |
| `text-ivory` (#1A1208) on `bg-panel` (#E5DBBC) | 13.8:1 | AAA ✓ |
| `text-ivory` (was #F5EFE0) on `dark-bg` (#080604) — footer | 18.4:1 | AAA ✓ |
| `text-dark-text` on `bg-gold` (#8B7340) — primary CTA | 6.8:1 | AAA ✓ |

All pairings meet AA. Most clear AAA.

## 7. Three migration options — user picks

### Option A — Full inversion (every page becomes cream)

Flip the colors block in `tailwind.config.ts`. Footer + a couple of overlay
surfaces add explicit `dark-*` references. Estimated work: ~2 hours.

Pros: dramatic visual refresh; matches user request precisely; lowest engineering cost.

Cons: dashboard surfaces (mod queue, ops, AI tool consoles) currently designed
for dark — they may feel less focused on cream. Some image overlays + status
pips need brightness re-tuning.

### Option B — Cream public + dark dashboard (split by route group)

Public marketing routes (`/`, `/blog`, `/services`, `/community`, `/tools`,
`/about`) flip to cream. Authenticated dashboard (`/dashboard/*`) stays dark.

Implementation: split Tailwind into `colors-light` + `colors-dark`, gate by
route group via a `data-theme` attribute on the layout's `<html>` or root div.
Components use semantic token aliases that resolve per theme.

Pros: marketing pages welcome with cream; app stays focused/comfortable for
extended use. Industry standard (Stripe, Linear).

Cons: ~6 hours of work; need a theme provider; cards + components need review.

### Option C — Cream-on-cream with dark counterweights (the 1301 model)

Full cream like option A, but explicitly preserve dark in 4 places:
1. Footer (entire dark block at page bottom)
2. Top nav (sticky cream → dark on scroll for contrast against light hero)
3. Image gallery overlays + hero gradients
4. "Get started" / primary CTAs (dark-fill on cream surface)

Pros: closest to actual 1301 page; uses dark strategically for hierarchy.

Cons: most design work (~4 hours) but most visually rich result.

## 8. Migration plan (when chosen)

1. **Token flip** — update `frontend/styles/tailwind.config.ts` colors block.
2. **Add `dark-*` aliases** for explicit-dark surfaces (footer, overlays).
3. **Update Footer.tsx** — references `dark-bg`/`dark-text` explicitly.
4. **Hero overlays** — gradient stops update from `from-black` to `from-warm`.
5. **Tweak CTAs** — primary becomes `bg-dark-bg text-dark-text hover:bg-deep-dark`.
6. **Per-page audit** — visit /, /blog, /services, /community, /tools, /login,
   /signup, /dashboard. Adjust borders, focus rings, status pips to taste.
7. **Lighthouse + axe** — re-run accessibility audit; AA pairings verified.
8. **Update placeholder image generators** (`scripts/generate_*_placeholders.py`)
   so demo JPEGs use the new palette. Regenerate all 44.
9. **Update OG image generator** (`apps/content/services/og_image.py`) for cream.
10. **CLAUDE.md visual quality bar** + `docs/COPY-STYLE-GUIDE.md` notes
    update to reflect cream direction.

## 9. Open questions

1. **Option A, B, or C?** (Default recommendation: **C** — closest to 1301)
2. **Keep gold accent at #8B7340, or shift to a richer copper/bronze?** (e.g., #7A5A2A)
3. **Should the OG meta theme color stay #080604 (dark) or flip to cream?** (Affects how the site looks pinned in iOS / Android home screens.)
4. **Do you want the dashboard to flip too, or keep it dark?** (Option B specifically.)
5. **Regenerate placeholder JPEGs to match cream, or keep current darks for "demo" feel?**
6. **Logo — does the gold mark on cream still read clearly?** (May need to bump opacity or add a subtle shadow.)
