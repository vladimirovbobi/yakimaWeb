"""Seed demo marketplace data. Idempotent. Categories must already be seeded."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import VendorProfile
from apps.marketplace.models import (BillingCadence, Bundle, BundleItem,
                                      Category, Lead, LeadStatus, Package,
                                      PackageTier, Review, Service)


User = get_user_model()


VENDORS = [
    {
        "email":    "demo-photog@yakimaweb.local",
        "business": "Sunlit Lens Real Estate Photography",
        "tagline":  "Bright, clean, sells fast.",
        "category": "real-estate-photography",
        "service":  "Real Estate Photo Package",
        "service_desc": (
            "Full interior and exterior shoot for residential listings. Edited delivery "
            "within 24 hours. MLS-ready and social-ready exports included."
        ),
        "packages": [
            ("basic",    "Basic",    "Up to 25 photos, exterior + key interiors.",     Decimal("199")),
            ("standard", "Standard", "Up to 40 photos, twilight exterior, drone hero.", Decimal("349")),
            ("premium",  "Premium",  "Up to 60 photos, drone, twilight, virtual tour.", Decimal("549")),
        ],
    },
    {
        "email":    "demo-lender@yakimaweb.local",
        "business": "Cascade Mortgage of Central WA",
        "tagline":  "Conventional, FHA, VA — local underwriting.",
        "category": "conventional",
        "service":  "Pre-Approval Consultation",
        "service_desc": (
            "Free 45-minute consultation reviewing credit, debt-to-income, and the loan "
            "products that match. Hard pre-approval letter delivered same day."
        ),
        "packages": [
            ("basic",    "Quick Letter",     "Pre-qual letter from soft pull.",          Decimal("0")),
            ("standard", "Hard Pre-Approval", "Hard pull, full letter, lender call.",    Decimal("0")),
            ("premium",  "Buyer Concierge",  "Pre-approval + rate-watch + buyer prep.",  Decimal("0")),
        ],
    },
    {
        "email":    "demo-junk@yakimaweb.local",
        "business": "Valley Junk & Hauling",
        "tagline":  "Same-week clean-outs, transparent pricing.",
        "category": "junk-removal",
        "service":  "Listing Clean-Out",
        "service_desc": (
            "Full residential clean-out for listings, estate sales, and post-eviction "
            "properties. Includes haul, recycle, and broom-clean handoff."
        ),
        "packages": [
            ("basic",    "Half Truck",  "Up to 8 cubic yards.",                   Decimal("295")),
            ("standard", "Full Truck",  "Up to 16 cubic yards, broom-clean.",     Decimal("525")),
            ("premium",  "Multi-Truck", "Multi-truck full estate clean-out.",     Decimal("950")),
        ],
    },
    {
        "email":    "demo-staging@yakimaweb.local",
        "business": "Hearth & Home Virtual Staging",
        "tagline":  "Empty rooms, sold listings.",
        "category": "virtual-staging",
        "service":  "Virtual Staging Bundle",
        "service_desc": (
            "Empty-room photographs returned with realistic, market-appropriate furnishings. "
            "Multiple style variations per room available on request."
        ),
        "packages": [
            ("basic",    "Single Room",      "1 room, 1 style.",        Decimal("39")),
            ("standard", "Whole Listing",    "Up to 6 rooms, 1 style.", Decimal("199")),
            ("premium",  "Style Variations", "6 rooms, 3 styles each.", Decimal("449")),
        ],
    },
    {
        "email":    "demo-marketing@yakimaweb.local",
        "business": "Lower Valley Brand Studio",
        "tagline":  "Realtor branding that does not look like everyone else.",
        "category": "branding",
        "service":  "Realtor Brand Refresh",
        "service_desc": (
            "Logo, color system, and printable identity assets for solo agents and small "
            "teams. Two rounds of revision included."
        ),
        "packages": [
            ("basic",    "Logo",         "Logo + color palette.",                       Decimal("450")),
            ("standard", "Identity",     "Logo, palette, business cards, listing flyer.", Decimal("950")),
            ("premium",  "Full Brand",   "Identity + social templates + brand guide.",  Decimal("1850")),
        ],
    },
]


BUNDLE_VENDOR_EMAIL = "demo-photog@yakimaweb.local"
BUNDLE_NAME = "Listing Launch Pro"


def _ensure_user(email: str, full_name: str) -> User:
    user, created = User.objects.get_or_create(
        email=email,
        defaults={"full_name": full_name, "is_vendor": True, "role": "vendor"},
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    return user


def _ensure_vendor(user: User, business: str, tagline: str) -> VendorProfile:
    profile, _ = VendorProfile.objects.get_or_create(
        user=user,
        defaults={
            "business_name": business,
            "slug": slugify(business)[:200],
            "status": VendorProfile.Status.ACTIVE,
            "tagline": tagline,
        },
    )
    return profile


def _ensure_buyer() -> User:
    return _ensure_user("demo-buyer@yakimaweb.local", "Demo Buyer")


class Command(BaseCommand):
    help = "Seed demo vendors, services, packages, bundles, leads, and reviews. Idempotent."

    def handle(self, *args, **opts):
        if not Category.objects.exists():
            self.stdout.write(self.style.ERROR(
                "No categories found — run `seed_categories` first."
            ))
            return

        now = timezone.now()
        services_created = 0
        packages_created = 0

        services_by_email: dict[str, Service] = {}

        for spec in VENDORS:
            user = _ensure_user(spec["email"], spec["business"])
            vendor = _ensure_vendor(user, spec["business"], spec["tagline"])
            category = Category.objects.filter(slug=spec["category"]).first()
            if category is None:
                continue

            service, was_created = Service.objects.get_or_create(
                vendor=vendor,
                title=spec["service"],
                defaults={
                    "category": category,
                    "description": spec["service_desc"],
                    "moderation_status": "approved",
                    "moderated_at": now,
                },
            )
            if was_created:
                services_created += 1
            services_by_email[spec["email"]] = service

            for tier, name, desc, price in spec["packages"]:
                _, p_created = Package.objects.get_or_create(
                    service=service,
                    tier=tier,
                    defaults={
                        "name":          name,
                        "description":   desc,
                        "price_low":     price,
                        "price_high":    price,
                        "delivery_days": 5 if tier == PackageTier.BASIC else 7,
                        "revisions":     1 if tier == PackageTier.BASIC else 2,
                        "features":      [],
                    },
                )
                if p_created:
                    packages_created += 1

        bundle_created = 0
        bundle_service = services_by_email.get(BUNDLE_VENDOR_EMAIL)
        if bundle_service is not None:
            bundle, was_created = Bundle.objects.get_or_create(
                vendor=bundle_service.vendor,
                name=BUNDLE_NAME,
                defaults={
                    "description": (
                        "Monthly retainer combining premium photography for two new listings, "
                        "plus a virtual-staging credit and one twilight reshoot."
                    ),
                    "price_total":     Decimal("799"),
                    "billing_cadence": BillingCadence.MONTHLY,
                    "min_term_months": 3,
                    "moderation_status": "approved",
                    "moderated_at": now,
                },
            )
            if was_created:
                bundle_created += 1
                BundleItem.objects.get_or_create(
                    bundle=bundle, service=bundle_service,
                    defaults={"quantity_per_period": 2,
                              "fulfillment_note": "Premium package per listing."},
                )

        buyer = _ensure_buyer()
        leads_created = 0
        for spec in VENDORS[:3]:
            service = services_by_email.get(spec["email"])
            if service is None:
                continue
            if Lead.objects.filter(buyer=buyer, vendor=service.vendor).exists():
                continue
            Lead.objects.create(
                vendor=service.vendor, buyer=buyer, service=service,
                message=f"Interested in {service.title}. Looking for a quote.",
                status=LeadStatus.PENDING,
            )
            leads_created += 1

        reviews_created = 0
        for spec in VENDORS[:3]:
            service = services_by_email.get(spec["email"])
            if service is None:
                continue
            won_lead, _ = Lead.objects.get_or_create(
                vendor=service.vendor, buyer=buyer, service=service,
                status=LeadStatus.WON,
                defaults={
                    "message": "Closed deal — ready to review.",
                    "won_at":  now,
                },
            )
            _, was_created = Review.objects.get_or_create(
                lead=won_lead,
                defaults={
                    "rating": 5,
                    "body":   "Professional, on-time, made my listing look great.",
                    "moderation_status": "approved",
                    "moderated_at": now,
                },
            )
            if was_created:
                reviews_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Marketplace seed: services={services_created}, packages={packages_created}, "
            f"bundles={bundle_created}, leads={leads_created}, reviews={reviews_created}."
        ))
