# Phase 7 — Social Integration

## Goal
YouTube channel videos + Shorts + Instagram posts surfaced on the platform without baking 3rd-party SDKs into the page.

## Done
- [ ] `SocialEmbed` model — provider (youtube/instagram), kind (video/short/post), external_id, title, thumb_url, published_at, sort_order
- [ ] Admin: paste a YouTube URL → server-side resolves to embed metadata (yt-dlp or oEmbed)
- [ ] Public `/videos/` page — grid of latest YouTube videos + Shorts
- [ ] Homepage section pulls 3 latest items
- [ ] Celery beat refreshes thumbnails + view counts daily
- [ ] No JS SDKs loaded — all served as `<iframe>` with `loading="lazy"` + privacy-enhanced mode

## Files (in apps/content/)
- `apps/content/models.py` — add `SocialEmbed`
- `apps/content/services/youtube.py` — oEmbed resolver
- `apps/content/services/instagram.py` — oEmbed resolver (or graph API later)
- `apps/content/tasks.py` — `refresh_social_embeds` beat task
- `templates/content/videos.html`
- `templates/content/_social_grid.html` — reusable on homepage

## Skills: caveman, copy-editing (channel taglines), security-review (3rd-party iframe boundary)
