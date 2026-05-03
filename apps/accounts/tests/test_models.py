"""User + RealtorProfile model tests."""
import pytest

from apps.accounts.models import (LicenseType, RealtorProfile, Role, User,
                                  VerificationStatus)


@pytest.mark.django_db
class TestUser:
    def test_email_login(self):
        u = User.objects.create_user(email="JANE@example.com", password="pa$$word-12345")
        assert u.email == "JANE@example.com"
        assert u.check_password("pa$$word-12345")
        assert u.role == Role.MEMBER
        assert not u.is_realtor

    def test_email_required(self):
        with pytest.raises(ValueError, match="Email is required"):
            User.objects.create_user(email="", password="x")

    def test_superuser(self):
        u = User.objects.create_superuser(email="admin@example.com", password="pa$$word-12345")
        assert u.is_staff and u.is_superuser

    def test_full_name_fallback(self, user):
        assert user.get_full_name() == user.email
        user.full_name = "Jane Smith"
        assert user.get_full_name() == "Jane Smith"
        assert user.get_short_name() == "Jane"


@pytest.mark.django_db
class TestRealtorProfileSignal:
    """Verify the post_save signal toggles is_realtor when status changes."""

    def test_pending_does_not_grant(self, user):
        RealtorProfile.objects.create(
            user=user, license_number="12345", license_type=LicenseType.BROKER,
            verification_status=VerificationStatus.PENDING,
        )
        user.refresh_from_db()
        assert not user.is_realtor

    def test_verified_grants_role(self, user):
        p = RealtorProfile.objects.create(
            user=user, license_number="12345", license_type=LicenseType.BROKER,
            verification_status=VerificationStatus.PENDING,
        )
        p.verification_status = VerificationStatus.VERIFIED
        p.save()
        user.refresh_from_db()
        assert user.is_realtor
        assert user.role == Role.REALTOR

    def test_revoked_strips_role(self, realtor):
        p = RealtorProfile.objects.create(
            user=realtor, license_number="12345", license_type=LicenseType.BROKER,
            verification_status=VerificationStatus.VERIFIED,
        )
        p.verification_status = VerificationStatus.REVOKED
        p.save()
        realtor.refresh_from_db()
        assert not realtor.is_realtor
        assert realtor.role == Role.MEMBER
