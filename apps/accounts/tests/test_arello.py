"""ARELLO client tests — mocked via responses library."""
import pytest
import responses
from django.test import override_settings

from apps.accounts.services.arello import (ARelloDown, ARelloRateLimited,
                                            verify_license)


@override_settings(ARELLO_BASE_URL="https://lvws.example.com",
                   ARELLO_API_KEY="test-key")
class TestVerifyLicense:
    @responses.activate
    def test_active_broker(self):
        responses.add(
            responses.GET,
            "https://lvws.example.com/api/v2/search",
            json={"count": 1, "results": [{
                "license_number": "12345",
                "jurisdiction": "WA",
                "license_type": "BROKER",
                "status": "ACTIVE",
                "first_name": "Jane",
                "last_name": "Smith",
                "expiration_date": "2026-12-31",
            }]},
            status=200,
        )
        rec = verify_license("12345", last_name="Smith")
        assert rec.status == "ACTIVE"
        assert rec.license_type == "BROKER"
        assert rec.expiration_date.year == 2026

    @responses.activate
    def test_not_found(self):
        responses.add(responses.GET, "https://lvws.example.com/api/v2/search",
                      json={"count": 0, "results": []}, status=200)
        rec = verify_license("99999")
        assert rec.status == "NOT_FOUND"

    @responses.activate
    def test_expired(self):
        responses.add(responses.GET, "https://lvws.example.com/api/v2/search",
                      json={"count": 1, "results": [{
                          "license_number": "12345", "jurisdiction": "WA",
                          "license_type": "BROKER", "status": "EXPIRED",
                      }]}, status=200)
        rec = verify_license("12345")
        assert rec.status == "EXPIRED"

    @responses.activate
    def test_suspended(self):
        responses.add(responses.GET, "https://lvws.example.com/api/v2/search",
                      json={"count": 1, "results": [{
                          "license_number": "12345", "jurisdiction": "WA",
                          "license_type": "BROKER", "status": "SUSPENDED",
                      }]}, status=200)
        rec = verify_license("12345")
        assert rec.status == "SUSPENDED"

    @responses.activate
    def test_rate_limited(self):
        responses.add(responses.GET, "https://lvws.example.com/api/v2/search",
                      json={"error": "rate_limited"}, status=429)
        with pytest.raises(ARelloRateLimited):
            verify_license("12345")

    @responses.activate
    def test_server_error(self):
        responses.add(responses.GET, "https://lvws.example.com/api/v2/search",
                      json={"error": "internal"}, status=503)
        with pytest.raises(ARelloDown):
            verify_license("12345")
