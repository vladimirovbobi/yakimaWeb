"""Smoke tests — every public page returns 200, base.html renders, healthz alive."""
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestPublicPages:
    @pytest.mark.parametrize("url_name", ["core:home", "core:about", "core:guidelines",
                                          "core:privacy", "core:terms"])
    def test_returns_200(self, client, url_name):
        r = client.get(reverse(url_name))
        assert r.status_code == 200

    def test_home_has_brand(self, client):
        r = client.get(reverse("core:home"))
        assert b"Yakima Real Estate Hub" in r.content

    def test_healthz(self, client):
        r = client.get("/healthz")
        assert r.status_code == 200
        assert b"ok" in r.content.lower()


@pytest.mark.django_db
class TestProfileAuth:
    def test_profile_redirects_anon(self, client):
        r = client.get(reverse("core:profile"))
        assert r.status_code == 302
        assert "/accounts/login" in r["Location"]
