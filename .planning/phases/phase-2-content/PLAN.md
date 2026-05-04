# Phase 2 — Content System

## Goal
Polymorphic Post (org / blog / landing) + threaded Comment + moderation hook + lead-magnet landing pages.

## Done
- [ ] Org staff can publish "yakimaweb" posts via Django admin
- [ ] Verified realtors can author + publish "blog" posts
- [ ] Members can comment + reply (1 level threading)
- [ ] Every Post + Comment goes through moderation pipeline
- [ ] Lead-magnet landing pages (placeholders) for Phase 3 tools
- [ ] SEO: sitemap.xml + JSON-LD BlogPosting + OG tags
- [ ] Tests + 5 new prompt-injection fixtures

## Models
- `Post(ModeratableMixin, TimeStampedModel)` — title, slug, post_type (org/blog/landing), author, body (markdown), excerpt, hero_image, published_at, view_count
- `Comment(ModeratableMixin, TimeStampedModel)` — post FK, author FK, body, parent FK (1-level threading)
- `Subscription` (newsletter) — placeholder for v2

## Streams
- A: Models + migrations + admin
- B: Markdown editor (TipTap or simple textarea + bleach) + moderation hook
- C: Public list + detail templates (vrov-new card pattern)
- D: SEO (sitemap, JSON-LD)
- E: Tests + adversarial fixtures

## Skills: caveman, copy-editing (post body sanitization), frontend-design (cards), security-review at end
