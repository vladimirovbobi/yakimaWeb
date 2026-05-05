# Feature audit — 2026-05-05

End-to-end audit of every public, authed, and back-office surface against the live
8-service stack (Caddy → Next.js 16 / Django REST API / Postgres / Redis / Celery
+ beat + img-worker / delivery). Verification was done by hitting endpoints from
inside the `api` container at `http://caddy` (Host: localhost) and re-rendering
every page after fixes.

## Severity counts

| Severity | Count | IDs |
|---|---|---|
| Blocker | 4 | FEAT-001, FEAT-002, FEAT-003, FEAT-004 |
| High | 5 | FEAT-005, FEAT-006, FEAT-007, FEAT-008, FEAT-009 |
| Medium | 6 | FEAT-010 .. FEAT-015 |
| Low | 3 | FEAT-016, FEAT-017, FEAT-018 |
| Polish | 4 | FEAT-019 .. FEAT-022 |

All Blocker + High findings have surgical fixes applied and verified live. Medium /
Low items either deferred (separate effort, see notes) or fixed in passing.

---

## Blockers (fixed)

### FEAT-001 — Forum sort=hot crashes the whole queryset
- **Where**: `apps/forum/api/views.py:43-67` (`PublicFlairThreadListView` + `_sort_threads`)
- **Repro**: `GET /api/public/v1/community/<flair>/threads/?sort=hot` → 500
  `AttributeError: 'list' object has no attribute 'order_by'`. CursorPagination tries
  `.order_by(*self.ordering)` on the Python list returned by hot-sort.
- **Fix**: Override `list()` on the view to short-circuit pagination when the queryset
  is materialised (sort=hot), serialising the truncated slice directly. Same logic
  applied to the new cross-flair endpoint (FEAT-002).
- **Verified**: `curl /api/public/v1/community/discussion/threads/?sort=hot` → 200
  with proper `{next, previous, results}` shape.

### FEAT-002 — Cross-flair `/community/threads/` endpoint missing
- **Where**: home page + community index call `/api/public/v1/community/threads/?sort=hot`
  (`frontend/app/(public)/page.tsx:107`, `frontend/app/(public)/community/page.tsx:69`),
  but only `/community/<flair>/threads/` existed.
- **Repro**: Both pages called a 404 endpoint, so home "Recent threads" + community
  "What's hot" rendered with no data ever.
- **Fix**: Added `PublicAllThreadsListView` at `/api/public/v1/community/threads/` plus
  `urls_public.py` route. Cross-flair listing with the same sort/limit semantics.
- **Verified**: Home page now renders 8 real threads from seed data; community index
  "Recent threads" populates with the hot list.

### FEAT-003 — Frontend FLAIRS used invented slugs (none matched DB)
- **Where**: `frontend/app/(public)/community/page.tsx:25-66`,
  `frontend/app/(public)/community/[flair]/page.tsx:12-45`. Frontend had
  `buying / selling / market / renting / ask / vendors / neighborhood / general`;
  DB seed has `question / discussion / help / local-news / market / show-tell / off-topic`
  (only `market` overlapped).
- **Repro**: Every flair card on `/community` linked to a 404 page. `/community/general`
  in the hero CTA pointed to nothing.
- **Fix**: Re-aligned frontend `FLAIRS` + `FLAIR_INFO` to match the seeded slugs and
  changed the hero CTAs to `/community/discussion`. Also fixed
  `[flair]/page.tsx` to call the correct `/community/<flair>/threads/` endpoint
  (was hitting the cross-flair endpoint with a `?flair=` query that didn't exist).
- **Verified**: `/community/discussion` lists threads; all cards on `/community`
  resolve to real flairs.

### FEAT-004 — `/api/v1/me/` never returned `is_staff` or `display_name`
- **Where**: `apps/accounts/api/serializers.py::PrivateUserSerializer` returned
  `full_name` only; `PublicUserSerializer` likewise. Frontend's `CurrentUser`
  type expected `display_name` + `is_staff`.
- **Repro**: Every staff dashboard guard read `if (!user.is_staff) redirect("/dashboard")` —
  always undefined → admin user permanently bounced from `/dashboard/mod`,
  `/dashboard/mod/queue`, `/dashboard/mod/stats`, `/dashboard/mod/escalations`,
  `/dashboard/mod/investigate`, and `/dashboard/ops`. Welcome banner showed
  "Welcome back, stranger" regardless of who logged in.
- **Fix**: Added `display_name` (aliased from `full_name`), `avatar_url` (absolute
  URL), `is_staff`, `is_superuser` to `PrivateUserSerializer`. Added `display_name`
  to `PublicUserSerializer` (which is used as nested `author` on all post / thread /
  comment / reply payloads, fixing display name everywhere downstream).
- **Verified**: `GET /api/v1/me/` now returns
  `{... "display_name": "Admin", "is_staff": true, "is_superuser": true ...}`.

---

## High (fixed)

### FEAT-005 — `ThreadCard` rendered `[object Object]` for the flair label
- **Where**: `frontend/components/forum/ThreadCard.tsx:7-27` had a hand-rolled
  `FLAIR_LABEL: Record<string, string>` and used `FLAIR_LABEL[thread.flair]` —
  but `thread.flair` is a `{slug, label, color}` object, so the lookup key
  coerced to the string `"[object Object]"`, falling back to the same string.
- **Fix**: Replaced the lookup with `thread.flair?.label || thread.flair?.slug || "Forum"`.
- **Verified**: cards now read "Discussion" / "Question" / etc.

### FEAT-006 — Thread detail page rendered `[object Object]` and 404'd back-link
- **Where**: `frontend/app/(public)/community/threads/[slug]/page.tsx` lines 64,
  82, 99, 101, 104. `thread.flair` was rendered directly (object) and used as
  href segment.
- **Fix**: Added `flairSlug` + `flairLabel` locals derived from `thread.flair`
  and threaded them through every place that previously stringified the object.
- **Verified**: Back-link on `/community/threads/<slug>` resolves to the real
  flair page.

### FEAT-007 — Dashboard home printed `[object Object]` for thread flair
- **Where**: `frontend/app/(dashboard)/dashboard/page.tsx:131` — `{t.flair} - {t.reply_count} replies`.
- **Fix**: `{t.flair?.label || t.flair?.slug || "Forum"}`.
- **Verified**: render check.

### FEAT-008 — Vendor profile page hit a 404 endpoint (`/services/vendors/<slug>/`)
- **Where**: `frontend/app/(public)/services/vendors/[slug]/page.tsx:25-54`,
  `frontend/app/(public)/services/page.tsx:62`. Frontend called
  `/api/public/v1/services/vendors/<slug>/` and `.../reviews/`, but the real path
  is `/api/public/v1/vendors/<slug>/` (no `services/` prefix).
- **Fix**: Updated both fetch URLs to `/api/public/v1/vendors/<slug>/` and the
  featured-vendor list to `/api/public/v1/vendors/?featured=1`. Reviews-by-vendor
  endpoint still doesn't exist server-side — `safeServerFetch` returns null and the
  page conditionally hides the section, so render is graceful (gap, not crash).
- **Verified**: `/services/vendors/yakima-home-edit` renders with the vendor card,
  services list, and contact aside.

### FEAT-009 — Forum thread/reply API returned `score` only, frontend wanted `vote_score` + `user_vote`
- **Where**: `apps/forum/api/serializers.py::ForumThreadListSerializer`,
  `ForumThreadDetailSerializer`, `ForumReplySerializer`. Frontend types in
  `frontend/lib/api/types.ts` use `vote_score` / `user_vote`; API used `score` /
  `viewer_vote`. Vote button on detail pages would always show `0` and the
  user's prior vote could never highlight.
- **Fix**: Added `vote_score = IntegerField(source="score")` aliases and
  `user_vote = SerializerMethodField()` (alongside the existing `viewer_vote`)
  on Thread detail + Reply serializers. Existing `score` / `viewer_vote` fields
  retained for backwards compatibility.
- **Verified**: Thread detail JSON now contains both `score` + `vote_score` and
  both `viewer_vote` + `user_vote`.

---

## Medium (mostly fixed)

### FEAT-010 — No `loading.tsx` siblings for server-fetching routes
- **Fix**: Added `frontend/components/layout/Skeleton.tsx` (PageSkeleton +
  SkeletonBar primitives, motion-safe). Added `loading.tsx` siblings at
  `(public)/blog`, `(public)/services`, `(public)/community`, `(dashboard)`.
  Brand-consistent gold-on-deep skeletons honoring `prefers-reduced-motion`.

### FEAT-011 — Empty states were plain `<p>` text everywhere
- **Fix**: Added `frontend/components/layout/EmptyState.tsx` (uses the 5 SVGs
  shipped at `frontend/public/img/empty/`). Wired into `dashboard/vendor/leads`
  + `dashboard/notifications`. Other empty list spots
  (community page, blog page) deferred — they have inline copy already, EmptyState
  upgrade is polish-tier.

### FEAT-012 — `/dashboard/realtor/posts` index page didn't exist
- **Where**: 4 places linked to `/dashboard/realtor/posts` (sidebar, dashboard
  home, post-edit redirect) but no page existed.
- **Fix**: Added `frontend/app/(dashboard)/realtor/posts/page.tsx` — feeds from
  `/api/v1/me/activity/?limit=50`, lists each post with title/date/edit link, uses
  EmptyState when empty with a CTA to `/dashboard/realtor/posts/new`.
- **Verified**: Page renders behind auth (307 redirect to /login when anonymous,
  as expected).

### FEAT-013 — Sitemap canonical URL was hard-coded to `:3000`
- **Where**: `frontend/app/sitemap.ts:4` falls back to `http://localhost:3000`
  when `NEXT_PUBLIC_SITE_URL` is unset; Caddy fronts on `:80`, so every
  `<loc>` in `sitemap.xml` had the wrong port.
- **Fix**: Added `NEXT_PUBLIC_SITE_URL: ${NEXT_PUBLIC_SITE_URL:-http://localhost}`
  to the frontend service in `docker-compose.yml`. Recommend production set
  this to `https://yakimaweb.com`.

### FEAT-014 — `mod` queue depth always shows `1` or `0`
- **Where**: `frontend/app/(dashboard)/mod/page.tsx:25` reads `count` (CursorPagination
  doesn't return it) then falls back to `results?.length` of a `?limit=1` query.
- **Status**: Documented, deferred. Real fix needs a server-side `count` endpoint
  (`/api/v1/mod/queue/count/`) or LimitOffsetPagination override on the queue.
  Not a crash — just a wrong number on a low-traffic stat.

### FEAT-015 — `/dashboard/realtor/verify` and `/dashboard/realtor/edit` are dead links
- **Where**: `frontend/app/(dashboard)/realtor/page.tsx:88, 106`. Both linked
  from the realtor dashboard but neither route exists.
- **Status**: Documented, deferred. Building a real verify wizard + edit form
  is a Sprint 4-shaped effort, not a surgical fix.

---

## Low

### FEAT-016 — Reply tree never nests
- **Where**: `frontend/app/(public)/community/threads/[slug]/ReplyTree.tsx`
  iterates `reply.replies` recursively, but the API returns a flat list of replies
  with `parent: null|<id>`. So nested threads always render flat.
- **Status**: Documented. Either client-side tree-build from `parent` ids, or
  server returns a `replies: []` field. Defer.

### FEAT-017 — Dev `DJANGO_OTP_REQUIRED_FOR_STAFF=True` makes ops dashboard inaccessible
- **Where**: `.env` ships with `True`, ops endpoints sit behind `RequiresOTP`
  permission. Without a TOTP device set up, every ops API returns 403.
  The `/dashboard/ops` page is currently a `<ComingSoon>` placeholder so the
  effect is masked.
- **Status**: Documented. Setting `DJANGO_OTP_REQUIRED_FOR_STAFF=False` in dev
  `.env` is the right call when ops UI ships.

### FEAT-018 — Vendor public detail serializer missing `bio`/`hero_url`/`logo_url`/`is_verified`/`service_area`/`rating_count`
- **Where**: `apps/marketplace/api/serializers.py::VendorDetailSerializer`. The
  vendor profile page `frontend/app/(public)/services/vendors/[slug]/page.tsx`
  reads these fields. They're all guarded by `&&` so the page renders, just
  without those sections.
- **Status**: Documented. Real fix is to widen the serializer + add the model
  fields where missing. Defer.

---

## Polish

### FEAT-019 — `/manifest.webmanifest` returns 404
- The frontend generates `/manifest.json` (Next 16 default). No code references
  `.webmanifest`. Test was misnamed; not a real bug.

### FEAT-020 — `/api/public/v1/posts/tags/` returns `[]`
- Tags endpoint works, just no seeded tags. Frontend handles empty.

### FEAT-021 — Tools landing missing `loading.tsx`
- The tools landing is fully static (no fetch), so loading.tsx is unnecessary.
  Skipped intentionally.

### FEAT-022 — `videos` page empty-state could use `EmptyState` component
- Currently a plain `<p>`. Defer to a content polish pass.

---

## Files modified

### Backend (4 files)
- `apps/accounts/api/serializers.py` — added `display_name`, `is_staff`,
  `is_superuser`, `avatar_url` on `PrivateUserSerializer`; `display_name` on
  `PublicUserSerializer`.
- `apps/forum/api/serializers.py` — added `vote_score` + `user_vote` aliases on
  thread/reply serializers (kept `score` + `viewer_vote` for back-compat).
- `apps/forum/api/views.py` — fixed `PublicFlairThreadListView.list()` to handle
  `_sort_threads` returning a Python list under sort=hot. Added
  `PublicAllThreadsListView` for cross-flair listing.
- `apps/forum/api/urls_public.py` — registered `/community/threads/` route for
  the new view.

### Frontend (10 files)
- `frontend/app/(public)/community/page.tsx` — re-aligned FLAIRS to seeded slugs;
  fixed hero CTA `/community/general` → `/community/discussion`.
- `frontend/app/(public)/community/[flair]/page.tsx` — re-aligned FLAIR_INFO;
  fixed endpoint to `/community/<flair>/threads/`.
- `frontend/app/(public)/community/threads/[slug]/page.tsx` — fixed
  `thread.flair` object handling on back-link, badge, JSON-LD context.
- `frontend/app/(public)/services/vendors/[slug]/page.tsx` — corrected the
  vendor detail + reviews API paths (`vendors/` not `services/vendors/`).
- `frontend/app/(public)/services/page.tsx` — fixed featured-vendors path.
- `frontend/app/(dashboard)/dashboard/page.tsx` — fixed `t.flair` rendering.
- `frontend/components/forum/ThreadCard.tsx` — fixed flair-as-object lookup.
- `frontend/app/(dashboard)/notifications/NotificationsClient.tsx` — wired
  `EmptyState`.
- `frontend/app/(dashboard)/vendor/leads/page.tsx` — wired `EmptyState`.
- `docker-compose.yml` — added `NEXT_PUBLIC_SITE_URL`.

### New files (8)
- `frontend/components/layout/Skeleton.tsx` — `<PageSkeleton>` primitive.
- `frontend/components/layout/EmptyState.tsx` — branded empty-state block.
- `frontend/app/(public)/blog/loading.tsx`
- `frontend/app/(public)/services/loading.tsx`
- `frontend/app/(public)/community/loading.tsx`
- `frontend/app/(dashboard)/loading.tsx`
- `frontend/app/(dashboard)/realtor/posts/page.tsx` — my-posts list.
- `docs/FEATURE-AUDIT-2026-05-05.md` — this file.

---

## Top 3 deferred items + reasons

1. **Vendor public detail serializer expansion (FEAT-018)** — adding
   `bio`/`hero_url`/`logo_url`/`is_verified`/`service_area`/`rating_count`
   needs both serializer fields and (for `hero_url`/`logo_url`/`service_area`)
   model columns. Touches migrations + storage. >100 LOC, deferred per audit
   rules.
2. **Realtor verify + edit pages (FEAT-015)** — `/dashboard/realtor/verify`
   needs a real form + ARELLO submission flow, `/dashboard/realtor/edit` needs
   a profile editor. Each is a Sprint-shaped feature, not a bug fix.
3. **Reply tree nesting (FEAT-016)** — currently API returns flat replies with
   `parent` id; the UI iterates a non-existent `replies` array. Real fix needs
   either a server-side tree assembler in the replies serializer or client-side
   tree-build. Deferred — replies render correctly flat, just lack indentation.

---

## Test impact

`pytest -q apps/forum apps/accounts apps/content` → **50 passed, 0 failed**
(the surfaces I changed).

`pytest -q` over the full suite → **264 passed, 3 failed**. The 3 failures are
all in `apps/tools/tests/test_flyer_pdf.py` and `test_flyer_generator.py` and
involve mocked PDF backends; they're unrelated to anything in this audit
(verified by stash/rebuild and by grepping the failing test bodies — none
reference `is_staff`, `display_name`, `vote_score`, or any forum/account
serializer change). Pre-existing flake/regression in the flyer feature.

---

## Verification log (sample)

```
$ docker compose exec -T api curl -s -H "Host: localhost" \
    "http://caddy/api/public/v1/community/threads/?sort=hot" | jq '.results[0] | keys'
[
  "author", "created_at", "flair", "id", "last_activity_at",
  "locked", "pinned", "reply_count", "score", "slug", "title", "vote_score"
]

$ docker compose exec -T api curl -s -H "Host: localhost" -b /tmp/cookies.txt \
    "http://caddy/api/v1/me/" | jq 'keys'
[
  "avatar", "avatar_url", "created_at", "display_name", "email",
  "full_name", "id", "is_realtor", "is_staff", "is_superuser",
  "is_vendor", "last_seen", "role"
]

$ for p in / /community /community/discussion /blog /services \
           /services/yakima-home-edit-decluttering-consultation \
           /services/vendors/yakima-home-edit; do
    docker compose exec -T api curl -s -o /dev/null -w "%{http_code}\n" \
      -H "Host: localhost" "http://caddy${p}"
  done
200, 200, 200, 200, 200, 200, 200
```
