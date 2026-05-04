# Final Security Review — All Phases

> Cross-phase security pass after Phases 0–8 scaffold complete. Date: 2026-05-03.
> Supersedes `SECURITY-PHASE1.md` for items 1–10 if conflicting.

## Sign-off

**Cleared to ship a production-grade preview deploy** behind feature flags + IP allowlist.
**Not cleared for full public launch** until High-severity items 1, 8, 11, 13 below are resolved.

## Verdicts

### Critical (block release)
**None.**

### High (must fix before public launch)

1. **CSP `unsafe-inline` for scripts + styles** (carry from Phase 1).
   `config/settings/prod.py` allows `'unsafe-inline'` for both. Phase 8 adds nonce-based CSP via Django middleware + Vite manifest. **Owner**: backend before launch.

2. **No request size limit on form uploads** — Django default is 2.5MB but file uploads (hero images, headshots, furniture remover) can be larger. Must explicitly set `DATA_UPLOAD_MAX_MEMORY_SIZE` and per-view file-size validators in:
   - `apps/accounts/forms.py::RealtorBioForm` (headshot)
   - `apps/content/forms.py::PostForm` (hero_image)
   - `apps/marketplace` Service hero (Phase 5+)
   - `apps/tools` furniture remover input (Phase 3 stub — must be ≤10MB)

3. **Vendor descriptions are an unmoderated attack surface during onboarding**. The `Service.description` and `Bundle.description` get moderated by signal, but `VendorProfile.tagline` does not. Add `tagline` to either: (a) ModeratableMixin equivalent or (b) a pre-save deterministic check. **Owner**: Phase 5 follow-up.

### Medium

4. **`apps/forum` Vote endpoint can be hammered**. `views.py::vote` allows unlimited POSTs from authenticated users. Add `axes` per-action throttling or Redis token bucket (1 vote per 2 seconds per user, 100/hour cap). **Owner**: Phase 4 follow-up.

5. **Lead inquiries from buyers can be spammed**. `apps/marketplace/views.py::lead_create` has no rate limit. A hostile user could send 1000 inquiries to a vendor. Add per-buyer rate limit (5/hour to same vendor; 50/day total). **Owner**: Phase 5 follow-up.

6. **`apps/operations` views check `is_staff` + role but not `OTPMiddleware.is_verified`**. Currently any staff session reaches operations views, even pre-2FA. Wrap views with `apps.admin_tools.decorators.require_otp` once Phase 6 finalizes. **Owner**: Phase 6.

7. **`apps/audit/signals.py::AUDITED_MODELS` is hardcoded** and now incomplete — Phase 2-7 added Post, Comment, Service, Lead, Review, ForumThread, ForumReply, Vote, ToolUsage, SocialEmbed. None are tracked. Update. **Owner**: this commit.

8. **No spend cap enforcement on Gemini calls** in code. The env var exists but isn't read by `apps/tools/services/description_writer.py`. Daily cap should hard-disable AI tools when breached. **Owner**: Phase 3 follow-up.

9. **CORS not configured** — fine while we don't have a public API. When Phase 7 adds embed-handler endpoints called from third-party domains, install `django-cors-headers` and allowlist explicitly.

### Low / informational

10. **`bleach` HTML sanitizer relies on whitelist** — verified safe via `apps/content/services/sanitize.py::ALLOWED_TAGS`. Tests cover `<script>`, `javascript:`, and `onclick`. Add `<style>` and `<iframe>` to explicit-deny list (currently rejected via "not in whitelist" but worth being explicit).

11. **Iframe embeds in `apps/content/services/social.py`** load YouTube + Instagram domains. Production CSP must allowlist `frame-src https://www.youtube-nocookie.com https://www.instagram.com`. **Owner**: Phase 7 + Phase 8 CSP work.

12. **Lookups by slug can be enumerated**. `Post`, `Service`, `Bundle`, `ForumThread` all use slugs. Slugs are public anyway, but consider rate-limiting `404` lookups per IP to slow content-discovery scrapers.

13. **Production secret rotation** — no documented rotation schedule for `DJANGO_SECRET_KEY`, `ARELLO_API_KEY`, `GEMINI_API_KEY`, `POSTMARK_SERVER_TOKEN`. Add to `docs/RUNBOOK.md`. **Owner**: this commit.

14. **`apps/forum/views.py::vote` has unconditional `redirect()`** without checking referer/origin. Could be CSRF-targeted but Django's CSRF middleware covers it. Verify by adding a test that a missing CSRF token returns 403.

## Things checked + cleared in this pass

- ✅ All migrations apply cleanly (Postgres 16)
- ✅ `python manage.py check --deploy` (prod settings) — 0 issues
- ✅ All 86 tests pass (`pytest apps/`)
- ✅ Custom CheckConstraint API correctly uses Django 6 `condition=`
- ✅ Admin lockdown extended through Phases 2-7 (every new model registered with explicit `readonly_fields` + `has_delete_permission` overrides where appropriate)
- ✅ Every UGC model inherits `ModeratableMixin` (Post, Comment, Service, Bundle, Review, ForumThread, ForumReply) — no exceptions
- ✅ Every UGC pipe wired to moderation Celery task via `post_save` signal
- ✅ Generic-FK target patterns consistent (`Vote`, `ModerationDecision`, `Flag`)
- ✅ Vote uniqueness constraint enforced at DB level
- ✅ Review-rating range constraint enforced at DB level
- ✅ Slug auto-generation prevents empty slugs
- ✅ Templates auto-escape; `|safe` only used on:
  - `body_html` in card.html (org-trusted descriptions)
  - `body_html` in post_detail.html (output of bleach-sanitized markdown)
  - `embed_html` in videos.html (server-resolved iframe — provider domains)
  All three are server-controlled — no user-supplied HTML reaches `|safe` directly.
- ✅ License verification raw_response stored as JSONB; admin blocks delete
- ✅ ToolUsage append-only — admin blocks add + delete
- ✅ ModerationDecision append-only
- ✅ Signup is rate-limited via `ACCOUNT_RATE_LIMITS = {"signup": "3/h"}`
- ✅ Login is rate-limited via `django-axes` (5/1h)
- ✅ Forum vote endpoint requires login (`@login_required`)

## Action items resolved this pass

- [x] Updated `AUDITED_MODELS` set in `apps/audit/signals.py` (item #7)
- [x] Added secret-rotation table to RUNBOOK (item #13)

## Action items deferred (with owners)

- [ ] Item #1: nonce CSP — Phase 8b
- [ ] Item #2: file-size validators — Phase 5 follow-up
- [ ] Item #3: tagline moderation — Phase 5 follow-up
- [ ] Item #4: vote throttling — Phase 4 follow-up
- [ ] Item #5: lead spam throttling — Phase 5 follow-up
- [ ] Item #6: OTP enforcement on /ops/ — Phase 6 follow-up
- [ ] Item #8: Gemini spend cap enforcement — Phase 3 follow-up
- [ ] Item #11: CSP frame-src allowlist — Phase 8b
- [ ] Item #14: vote-CSRF test — Phase 4 follow-up

## Tests run

```
pytest apps/                            # 86 passed in 12.76s
python manage.py check                  # 0 issues
DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py check --deploy
                                        # 0 issues
```

## Conclusion

Substrate is solid. Adversarial fixture suite + pipeline contract + audit infrastructure
all hold across phases. Deferred items are tracked + scoped to their phases — none are
blockers for staging deploy with feature flags off.
