# Seed assets — content imagery pipeline

Sprint 1 deliverable. How to bulk-fetch CC0/CC-BY imagery for placeholder content
(blog hero images, vendor portfolios, forum thread show-and-tell). Pillow-based
brand placeholders live one directory up in `scripts/`; this directory is for
**content-photography placeholders** that fill out blog posts and vendor
listings before real photography arrives.

## Why this is separate

The `scripts/` parent directory generates **brand assets** (favicons, hero
placeholders, furniture-remover samples) — small, deterministic, always
regenerable from Pillow primitives.

This directory handles **content placeholders** — real-looking photography
sourced from CC0/CC-BY libraries. These are larger, slower to fetch, and we
cache them locally so the seed commands have stable references.

## Pipeline

1. **Source.** [Pexels API](https://www.pexels.com/api/) (CC0, free for commercial use,
   200/hr default rate limit, no attribution required but courtesy attribution
   preferred). Alternative: [Unsplash API](https://unsplash.com/developers).
2. **Fetch.** `python scripts/seed_assets/fetch_pexels.py --queries queries.json`
   pulls images by category, saves to `seed_assets/cache/`. Idempotent —
   skips already-downloaded.
3. **Stage.** Upload to Cloudflare R2 bucket `yakimaweb-seed/` (or for dev,
   serve from `frontend/public/seed/`). Keep a manifest mapping
   `{category} → [url1, url2, ...]`.
4. **Use in seed.** Seed commands look up the manifest and assign URLs to
   `Post.hero_image`, `Service.hero_image`, vendor portfolio fields, etc.

## Categories needed

Map to the subjects that appear in the seed data:

| Category | Search terms |
|---|---|
| `blog/market` | "real estate market", "house keys", "for sale sign" |
| `blog/neighborhood` | "small town main street", "residential street" |
| `blog/finance` | "calculator paper", "mortgage signing" |
| `blog/listing-prep` | "staged living room", "kitchen renovation" |
| `blog/inspection` | "home inspection", "flashlight basement" |
| `vendor/photography` | "interior wide angle", "twilight exterior" |
| `vendor/staging` | "modern living room", "minimal bedroom" |
| `vendor/landscaping` | "manicured front yard", "mulched garden bed" |
| `vendor/cleaning` | "clean kitchen counters", "sparkling sink" |
| `vendor/lending` | "mortgage paperwork", "couple at desk" |
| `vendor/tech` | "laptop keyboard", "office workspace" |
| `forum/show-tell` | "real estate drone", "twilight house exterior" |
| `community/avatars` | "friendly portrait professional" (×40) |

Build `scripts/seed_assets/queries.json` from this table.

## Future work (deferred)

- `scripts/seed_assets/fetch_pexels.py` — wrap the Pexels API. Take queries.json,
  emit `seed_assets/cache/{category}/{i}.jpg` and a manifest.
- `scripts/seed_assets/upload_to_r2.py` — sync `cache/` to R2.
- `scripts/seed_assets/verify_manifest.py` — validate that every category has
  at least N images.

For Sprint 1 the seed commands run without hero-image URLs (gradient fallback
inside `CuratedFeed`'s `StoryCard` handles missing imagery gracefully). The
Pexels fetcher is a Sprint 2 polish task.

## Replace before launch

All content imagery sourced from this pipeline is **CC0/CC-BY stock**. Real
launch must replace with photographer-supplied or platform-generated art per
the brand checklist in `frontend/README.md`.
