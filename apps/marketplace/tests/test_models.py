"""Marketplace model + constraint tests."""
import pytest
from django.db import IntegrityError

from apps.accounts.models import VendorProfile
from apps.marketplace.models import (Bundle, Category, Lead, LeadStatus, Package,
                                      PackageTier, Review, Service)


@pytest.fixture
def vendor(realtor):
    return VendorProfile.objects.create(user=realtor, business_name="Cascade Photography",
                                          slug="cascade-photography", status="active")


@pytest.fixture
def category(db):
    return Category.add_root(slug="photography", label="Photography")


@pytest.fixture
def service(vendor, category):
    return Service.objects.create(
        vendor=vendor, category=category, title="Real Estate Photography",
        description="x" * 200, response_time_hours=24,
    )


@pytest.mark.django_db
class TestService:
    def test_slug_auto(self, service):
        assert service.slug == "cascade-photography-real-estate-photography"

    def test_price_from_picks_lowest(self, service):
        Package.objects.create(service=service, tier=PackageTier.PREMIUM, name="P",
                                description="x", price_low=500, price_high=500)
        Package.objects.create(service=service, tier=PackageTier.BASIC, name="B",
                                description="x", price_low=100, price_high=100)
        assert service.price_from == 100


@pytest.mark.django_db
class TestPackage:
    def test_unique_tier_per_service(self, service):
        Package.objects.create(service=service, tier=PackageTier.BASIC, name="B",
                                description="x", price_low=100, price_high=100)
        with pytest.raises(IntegrityError):
            Package.objects.create(service=service, tier=PackageTier.BASIC, name="B2",
                                    description="x", price_low=200, price_high=200)


@pytest.mark.django_db
class TestReview:
    def test_rating_range(self, vendor, user, service):
        lead = Lead.objects.create(vendor=vendor, buyer=user, service=service,
                                    message="x", status=LeadStatus.WON)
        with pytest.raises(IntegrityError):
            Review.objects.create(lead=lead, rating=10, body="x")

    def test_review_one_per_lead(self, vendor, user, service):
        lead = Lead.objects.create(vendor=vendor, buyer=user, service=service,
                                    message="x", status=LeadStatus.WON)
        Review.objects.create(lead=lead, rating=5, body="great")
        with pytest.raises(IntegrityError):
            Review.objects.create(lead=lead, rating=4, body="duplicate")


@pytest.mark.django_db
class TestBundle:
    def test_bundle_slug_auto(self, vendor):
        b = Bundle.objects.create(vendor=vendor, name="Listing Launch Pro",
                                    description="x", price_total=500, billing_cadence="monthly")
        assert "cascade-photography" in b.slug and "listing-launch-pro" in b.slug
