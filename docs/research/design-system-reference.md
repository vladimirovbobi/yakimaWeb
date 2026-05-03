# Design System Reference — vrov-new Audit

> Source of truth for Yakima Real Estate Hub visual language. Tokens, components, animations all ported (with adaptations for Django+HTMX+Alpine instead of React+Framer Motion).

## Reference project
`C:\Users\vladi\OneDrive\Desktop\Projects\vrov-new`

## Stack mapping

| vrov-new | yakimaWeb |
|---|---|
| React 19 + Vite | Django templates + Vite (for asset bundling) |
| React Router 7 | Django URLconf |
| Framer Motion 11 | **Motion One** (vanilla port of Framer Motion API) |
| `@radix-ui/*` components | HTMX + Alpine + headless Tailwind components |
| TypeScript | Python |
| Tailwind 3.4 | Tailwind 3.4 (same config tokens) |
| `tailwindcss-animate` plugin | same (works in any Tailwind setup) |
| Lucide React icons | **Lucide static SVGs** included via Django template tag |
| Lenis smooth scroll | Lenis (vanilla) |

## Color tokens (port verbatim to `tailwind.config.js`)

```js
// tailwind.config.js — colors section
colors: {
  black:    '#080604',  // page background
  deep:     '#0D0904',  // card background
  panel:    '#141008',  // raised surface
  warm:     '#1A1208',  // hover surface
  gold:     '#BFA06A',  // primary accent (buttons, links, badges)
  'gold-hi':'#DEC98A',  // hover/active state of gold
  'gold-dim':'#5A4A28', // disabled / borders / dividers
  ivory:    '#F5EFE0',  // primary text on dark
  mist:     '#CEC4A8',  // secondary text on dark
  dim:      '#706450',  // tertiary text / muted
}
```

## Shadows (port verbatim)

```js
boxShadow: {
  card:       '0 4px 6px -1px rgba(0,0,0,0.18), 0 2px 4px -2px rgba(0,0,0,0.12)',
  'card-hover':'0 20px 25px -5px rgba(0,0,0,0.35), 0 8px 10px -6px rgba(0,0,0,0.22)',
  hero:       '0 25px 50px -12px rgba(0,0,0,0.5)',
}
```

## Typography

- **Display headings** — `font-serif` class. vrov-new uses system serif fallback. **For yakimaWeb use Cormorant Garamond** (Google Fonts) — luxe, real-estate-appropriate, has weight range 300-700.
- **Body** — system sans (Tailwind default `font-sans`)
- **Labels / overlines** — uppercase + `tracking-[0.22em]` (extra letter-spacing). Use `text-xs text-mist uppercase tracking-[0.22em]` as the canonical label class.

```html
<!-- canonical heading -->
<h1 class="font-serif text-4xl md:text-5xl text-ivory">Headline</h1>

<!-- canonical label -->
<span class="text-xs text-mist uppercase tracking-[0.22em]">Featured Realtor</span>

<!-- canonical body -->
<p class="text-base text-mist leading-relaxed">Body text</p>
```

## Border radius scale

```js
borderRadius: {
  xs:  'calc(var(--radius) - 6px)',
  sm:  'calc(var(--radius) - 4px)',
  md:  'calc(var(--radius) - 2px)',
  lg:  'var(--radius)',
  xl:  'calc(var(--radius) + 4px)',
  '2xl':'calc(var(--radius) + 8px)',
}
// :root { --radius: 6px; }
```

## Animation tokens

### Easing
```css
/* Custom cubic from vrov-new — port to Tailwind via plugin or @utility */
--ease-luxe: cubic-bezier(0.16, 1, 0.3, 1);

/* Tailwind plugin */
addUtilities({
  '.ease-luxe': { 'transition-timing-function': 'cubic-bezier(0.16, 1, 0.3, 1)' }
});
```

### Custom keyframes (Tailwind extend.keyframes)
```js
keyframes: {
  fup: {
    '0%':   { opacity: '0', transform: 'translateY(26px)' },
    '100%': { opacity: '1', transform: 'translateY(0)' },
  },
  zoomout: {
    '0%':   { transform: 'scale(1.05)' },
    '100%': { transform: 'scale(1)' },
  },
},
animation: {
  'fade-up': 'fup 1s 0.3s ease both',
  'slow-zoom': 'zoomout 22s ease-out forwards',
}
```

## Pattern: ScrollReveal (Alpine + Motion One adaptation)

`vrov-new` uses Framer Motion `useInView` + `useAnimation`. Equivalent in Django+Alpine:

```html
<!-- templates/_components/_scroll_reveal.html -->
<div
  x-data="{ revealed: false }"
  x-intersect.once="revealed = true"
  :class="revealed ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-[30px]'"
  class="transition-all duration-500 ease-luxe motion-reduce:transition-none motion-reduce:opacity-100 motion-reduce:translate-y-0"
  style="--reveal-delay: {{ delay|default:'0ms' }}; transition-delay: var(--reveal-delay);"
>
  {{ slot }}
</div>
```

Required Alpine plugins:
- `@alpinejs/intersect` (for `x-intersect`)

Usage:
```html
{% include "_components/_scroll_reveal.html" with delay="200ms" %}
  <div class="card">Content reveals on scroll</div>
{% include "_components/_scroll_reveal.html" %}
```

## Pattern: Card hover (Tailwind groups)

vrov-new `PropertyCard` lifts -4px on hover, image scales 1.04x, border brightens, title text → gold-hi.

```html
<a href="..." class="group block bg-deep border border-gold/14 rounded-lg overflow-hidden
                     shadow-card hover:shadow-card-hover hover:-translate-y-1
                     hover:border-gold/35 transition-all duration-300 ease-luxe">
  <div class="aspect-[4/3] overflow-hidden">
    <img src="..." alt="..." class="w-full h-full object-cover
                                    group-hover:scale-[1.04]
                                    transition-transform duration-[1400ms] ease-luxe">
  </div>
  <div class="p-6 md:p-7 space-y-2">
    <h3 class="font-serif text-2xl text-ivory group-hover:text-gold-hi transition-colors">Title</h3>
    <p class="text-xs text-mist uppercase tracking-[0.22em]">Location</p>
    <p class="font-serif text-xl text-gold">$Price</p>
  </div>
</a>
```

## Pattern: Hero (full-width, gradient overlay, staggered text)

vrov-new `PropertyHero` — black bg with image fill, gradient overlay (black/80 → transparent), title + subtitle + meta stagger in over 0.6s.

```html
<!-- templates/_components/_hero.html -->
<section class="relative bg-black aspect-[3/2] md:h-[65vh]">
  <img src="{{ image }}" alt="" class="absolute inset-0 w-full h-full object-cover animate-slow-zoom">
  <div class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent"></div>
  <div class="absolute inset-0 flex flex-col justify-end p-6 md:p-10 max-w-7xl mx-auto">
    <p class="text-xs text-gold-hi uppercase tracking-[0.22em] animate-fade-up [animation-delay:200ms]">{{ overline }}</p>
    <h1 class="font-serif text-4xl md:text-6xl text-ivory drop-shadow-lg animate-fade-up [animation-delay:300ms]">{{ headline }}</h1>
    <p class="mt-3 text-lg text-mist max-w-2xl animate-fade-up [animation-delay:400ms]">{{ subhead }}</p>
  </div>
</section>
```

## Anti-patterns (do NOT copy)

- ❌ **GSAP** — installed in vrov-new but unused; don't add it. Motion One covers everything.
- ❌ **Global `scroll-behavior: smooth` on `<html>`** — vrov-new explicitly avoids this due to mobile jank. Use Lenis for smooth scroll if needed (opt-in via JS).
- ❌ **shadcn HSL CSS variables for brand tokens** — vrov-new has these as legacy. Brand tokens go in tailwind config directly.
- ❌ **Code-splitting every route** — vrov-new lazy-loads non-home routes. Django delivers HTML; this isn't relevant. For React islands, lazy-load inside the island only when the island has multiple distinct sub-tools.

## Tools / libraries to install (Phase 1 Stream B)

```json
// package.json
{
  "dependencies": {
    "alpinejs": "^3.14",
    "@alpinejs/intersect": "^3.14",
    "@alpinejs/focus": "^3.14",
    "motion": "^11.0",
    "htmx.org": "^2.0",
    "lenis": "^1.1"
  },
  "devDependencies": {
    "tailwindcss": "^3.4",
    "@tailwindcss/forms": "^0.5",
    "@tailwindcss/typography": "^0.5",
    "tailwindcss-animate": "^1.0",
    "vite": "^5.4",
    "autoprefixer": "^10.4",
    "postcss": "^8.4"
  }
}
```

## Reference component checklist (Phase 1 Stream B4)

Re-implement these vrov-new components as Django partials:

- [ ] `_button.html` (3 variants: gold-fill, gold-outline, ghost; 3 sizes: sm/md/lg)
- [ ] `_card.html` (default / image-top / horizontal)
- [ ] `_input.html` (text / email / textarea / select; with label, hint, error states)
- [ ] `_modal.html` (Alpine `x-data="{ open: false }"`, focus trap via @alpinejs/focus, ESC closes)
- [ ] `_hero.html` (per pattern above)
- [ ] `_scroll_reveal.html` (per pattern above)
- [ ] `_badge.html` (verified, role: realtor/vendor, status: active/pending/suspended)
- [ ] `_nav.html` (header nav with mobile hamburger drawer)
- [ ] `_footer.html` (link grid, social icons, copyright)

## Quality bar checklist (every page)

Each polished page in Phase 1 Stream G must satisfy:
- ✅ Uses tokens from this file (no off-palette colors)
- ✅ Uses `font-serif` for headlines, sans for body
- ✅ At least one ScrollReveal on scroll-into-view content
- ✅ Hover states on every interactive element (transition + ease-luxe)
- ✅ Mobile-first responsive (test at 375px, 768px, 1280px)
- ✅ Lighthouse mobile ≥ 95 perf, 100 a11y
- ✅ `prefers-reduced-motion` respected (transitions disabled)
- ✅ axe-core zero violations
