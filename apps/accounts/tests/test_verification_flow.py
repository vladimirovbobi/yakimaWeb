"""End-to-end verification flow tests — ARELLO mocked."""
import pytest
import responses

from apps.accounts.models import (CheckTrigger, LicenseType, RealtorProfile,
                                  VerificationStatus)
from apps.accounts.services.verification import run_verification

ARELLO_URL = "https://lvws.example.com/api/v2/search"


@pytest.fixture(autouse=True)
def _arello_env(settings):
    settings.ARELLO_BASE_URL = "https://lvws.example.com"
    settings.ARELLO_API_KEY = "test-key"
    settings.CELERY_TASK_ALWAYS_EAGER = True


@pytest.mark.django_db
class TestRunVerification:
    @pytest.fixture
    def profile(self, user):
        user.full_name = "Jane Smith"
        user.save()
        return RealtorProfile.objects.create(
            user=user, license_number="12345", license_type=LicenseType.BROKER,
        )

    @responses.activate
    def test_active_grants_verified(self, profile):
        responses.add(responses.GET, ARELLO_URL,
                      json={"count": 1, "results": [{
                          "license_number": "12345", "jurisdiction": "WA",
                          "license_type": "BROKER", "status": "ACTIVE",
                          "expiration_date": "2027-01-01",
                      }]}, status=200)
        check = run_verification(profile, triggered_by=CheckTrigger.SIGNUP)
        profile.refresh_from_db()
        profile.user.refresh_from_db()
        assert profile.verification_status == VerificationStatus.VERIFIED
        assert profile.verified_at is not None
        assert profile.user.is_realtor
        assert check.status == "ACTIVE"

    @responses.activate
    def test_revoked_strips_role(self, profile):
        responses.add(responses.GET, ARELLO_URL,
                      json={"count": 1, "results": [{
                          "license_number": "12345", "jurisdiction": "WA",
                          "license_type": "BROKER", "status": "ACTIVE",
                      }]}, status=200)
        run_verification(profile)
        profile.user.refresh_from_db()
        assert profile.user.is_realtor

        responses.replace(responses.GET, ARELLO_URL,
                          json={"count": 1, "results": [{
                              "license_number": "12345", "jurisdiction": "WA",
                              "license_type": "BROKER", "status": "REVOKED",
                          }]}, status=200)
        run_verification(profile)
        profile.refresh_from_db()
        profile.user.refresh_from_db()
        assert profile.verification_status == VerificationStatus.REVOKED
        assert not profile.user.is_realtor

    @responses.activate
    def test_arello_down_logs_no_grant(self, profile):
        responses.add(responses.GET, ARELLO_URL, json={}, status=503)
        check = run_verification(profile)
        profile.refresh_from_db()
        assert check.status == "DOWN"
        assert profile.verification_status == VerificationStatus.PENDING
