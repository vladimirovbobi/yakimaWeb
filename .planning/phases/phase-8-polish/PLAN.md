# Phase 8 — Production Polish

## Goal
SEO + perf + a11y + final security review. Everything ships green.

## Done
- [ ] Django sitemaps for posts + services + forum threads
- [ ] /robots.txt
- [ ] Schema.org JSON-LD on home + about + every Post + Service
- [ ] OG image generator (Pillow) for posts that don't ship one
- [ ] Lighthouse mobile ≥ 95 perf / 100 a11y / 100 best-practices / 100 SEO on home
- [ ] axe-core zero violations on key pages
- [ ] Full security review pass (run security-review skill against all phases)
- [ ] Brotli + gzip via Whitenoise; image-resize via Cloudflare worker
- [ ] CSP nonces wired (drop unsafe-inline)
- [ ] All tests green (pytest + Playwright)

## Skills
- `/security-review` — full diff
- `/superpowers:verification-before-completion` — every claim verified
