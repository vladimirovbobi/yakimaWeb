"""LeadMessage moderation + signal coverage."""
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from apps.accounts.models import VendorProfile
from apps.marketplace.models import (
    Category,
    Lead,
    LeadMessage,
    LeadStatus,
    Service,
)

User = get_user_model()


@pytest.fixture
def buyer(db):
    return User.objects.create_user(email="buyer@example.com", password="pa$$word-12345")


@pytest.fixture
def vendor_user(db):
    return User.objects.create_user(email="vendor@example.com", password="pa$$word-12345",
                                     is_vendor=True)


@pytest.fixture
def vendor(vendor_user):
    return VendorProfile.objects.create(
        user=vendor_user, business_name="Cascade Photo", slug="cascade-photo",
        status="active",
    )


@pytest.fixture
def category(db):
    return Category.add_root(slug="photography", label="Photography")


@pytest.fixture
def service(vendor, category):
    return Service.objects.create(
        vendor=vendor, category=category, title="Real Estate Photography",
        description="x" * 200, response_time_hours=24,
    )


@pytest.fixture
def lead(vendor, buyer, service):
    return Lead.objects.create(
        vendor=vendor, buyer=buyer, service=service,
        message="hi please quote me", status=LeadStatus.PENDING,
    )


@pytest.mark.django_db
class TestLeadMessageMixin:
    def test_default_moderation_status_is_pending(self, lead, buyer):
        with patch("apps.marketplace.signals.moderate_content") as mc:
            mc.delay = lambda *a, **k: None
            m = LeadMessage.objects.create(lead=lead, sender=buyer, body="hello there")
        assert m.moderation_status == "pending"
        assert m.moderation_score is None
        assert m.moderated_at is None

    def test_moderation_signal_fires_on_create(self, lead, buyer):
        with patch("apps.marketplace.signals.moderate_content") as mc:
            mc.delay = mc
            m = LeadMessage.objects.create(lead=lead, sender=buyer, body="hello there")
        assert mc.called
        # The signal should have been called with the LeadMessage's PK.
        args, kwargs = mc.call_args
        assert args[1] == m.pk
        assert kwargs.get("text_attr") == "body"
        assert kwargs.get("context") == "lead_message"

    def test_moderation_signal_skips_blank_body(self, lead, buyer):
        with patch("apps.marketplace.signals.moderate_content") as mc:
            mc.delay = mc
            LeadMessage.objects.create(lead=lead, sender=buyer, body="   ")
        assert not mc.called
