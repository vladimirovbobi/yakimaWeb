"""Smoke tests — Django still serves /healthz, /sitemap.xml, /robots.txt post-DEB-002.

Marketing pages (/, /about, /guidelines, /privacy, /terms) are owned by Next.js
and tested via Playwright in frontend/tests/e2e/. The /accounts/profile/ route
moved to Next.js (/dashboard) gated by JWT cookie middleware.
"""
import pytest


@pytest.mark.django_db
class TestServerSurfaces:
    def test_healthz(self, client):
        r = client.get("/healthz")
        assert r.status_code == 200
        assert b"ok" in r.content.lower()

    def test_robots_txt(self, client):
        r = client.get("/robots.txt")
        assert r.status_code == 200

    def test_sitemap_xml(self, client):
        r = client.get("/sitemap.xml")
        assert r.status_code == 200
        assert b"<urlset" in r.content
