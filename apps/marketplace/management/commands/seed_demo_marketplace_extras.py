"""Extended marketplace seed: 20 more vendors + services + packages + bundles + leads + reviews.

Idempotent — safe to re-run on top of `seed_demo_marketplace`. Sprint 1 deliverable.
Brings the vendor surface to 25+ across the full category tree.
"""
from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import VendorProfile
from apps.marketplace.models import (
    BillingCadence,
    Bundle,
    BundleItem,
    Category,
    Lead,
    LeadStatus,
    Package,
    PackageTier,
    Review,
    Service,
)

User = get_user_model()


EXTRA_VENDORS = [
    # category-slug, business, tagline, service title, service desc, [(tier, name, desc, price)]
    ("drone-photography",
     "Skyline Aerials Yakima",
     "Drone hero shots for the listings that earn them.",
     "Drone Photo & Video Pack",
     "FAA-certified drone photography for real estate listings. Stills + cinematic flyover video, color-graded for MLS and social.",
     [("basic", "Stills Only", "8 stills, color-graded.", Decimal("145")),
      ("standard", "Stills + Reel", "12 stills + 30s reel.", Decimal("245")),
      ("premium", "Full Cinematic", "Stills + 30s + 60s cinematic + raw delivery.", Decimal("395"))]),

    ("twilight-photography",
     "Golden Hour Studio",
     "Twilight photos for the listings that deserve a hero shot.",
     "Twilight Photography Add-On",
     "Twilight exterior + interior photography. Best paired with a daytime shoot.",
     [("basic", "Exterior Only", "1 hero + 4 supporting shots.", Decimal("165")),
      ("standard", "Exterior + Interior", "1 hero + 4 ext + 6 int.", Decimal("265")),
      ("premium", "Twilight Full", "Twilight + drone + retouching.", Decimal("445"))]),

    ("3d-tour",
     "Walkthrough Yakima",
     "Matterport tours, ready in 24 hours.",
     "Matterport 3D Tour",
     "Full Matterport scan with embeddable tour link. Floor plan extraction included.",
     [("basic", "Up to 1500 sqft", "Tour + floor plan.", Decimal("199")),
      ("standard", "Up to 3000 sqft", "Tour + floor plan + measurements.", Decimal("349")),
      ("premium", "Over 3000 sqft", "Tour + floor plan + measurements + dollhouse export.", Decimal("549"))]),

    ("conventional",
     "Yakima Federal Mortgage Group",
     "Local underwriting, local timelines.",
     "Conventional Loan Pre-Approval",
     "Full conventional pre-approval with local underwriting. Hard credit pull, lender letter same business day.",
     [("basic", "Pre-Qual", "Soft pull pre-qual letter.", Decimal("0")),
      ("standard", "Pre-Approval", "Hard pull, full underwriting review.", Decimal("0")),
      ("premium", "Concierge", "Pre-approval + rate watch + buyer prep meeting.", Decimal("0"))]),

    ("va",
     "Cascade VA Lending Specialists",
     "VA loan specialists for Central Washington veterans.",
     "VA Loan Pre-Approval",
     "VA loan pre-approval with COE assistance. Specialists in VA-specific appraisal nuances.",
     [("basic", "Quick Letter", "Initial pre-qual + COE check.", Decimal("0")),
      ("standard", "Full Pre-Approval", "Hard pull + appraisal-prep consultation.", Decimal("0")),
      ("premium", "Concierge", "Pre-approval + buydown analysis + buyer prep.", Decimal("0"))]),

    ("fha",
     "Tri-County FHA Group",
     "FHA loans for first-time buyers.",
     "FHA Pre-Approval",
     "FHA loan pre-approval with first-time buyer education. Down payment assistance program guidance.",
     [("basic", "Pre-Qual", "Soft pull + DPA program review.", Decimal("0")),
      ("standard", "Pre-Approval", "Hard pull + appraisal-risk review.", Decimal("0")),
      ("premium", "Concierge", "Full prep + DPA application support.", Decimal("0"))]),

    ("cleaning",
     "Bright Valley Cleaning Co.",
     "Move-out and listing-prep cleaning.",
     "Listing Prep Deep Clean",
     "Full residential deep clean prior to listing photos. Inside windows, oven, appliances.",
     [("basic", "Standard Clean", "Up to 1500 sqft.", Decimal("245")),
      ("standard", "Deep Clean", "Up to 2500 sqft, inside appliances.", Decimal("385")),
      ("premium", "Move-Out Restore", "Full restore + carpet steam.", Decimal("595"))]),

    ("painting",
     "Mt. Adams Painting & Coatings",
     "Interior touch-ups and full repaints.",
     "Pre-Listing Paint Refresh",
     "Pre-listing touch-up paint and full-room repaints. Same-week turnaround for most jobs.",
     [("basic", "Touch-Up Only", "Up to 4 areas.", Decimal("345")),
      ("standard", "Single Room", "1 room, prep + paint.", Decimal("695")),
      ("premium", "Whole Interior", "Up to 1800 sqft, neutral palette.", Decimal("2950"))]),

    ("landscaping",
     "Yakima Curb Appeal Co.",
     "Front-yard refreshes that make showings work.",
     "Curb Appeal Refresh",
     "Front-yard cleanup, edging, mulch, seasonal flower install. One-day turnaround.",
     [("basic", "Cleanup Only", "Trim + edge + haul.", Decimal("245")),
      ("standard", "Refresh", "Cleanup + mulch + seasonal flowers.", Decimal("445")),
      ("premium", "Full Front Yard", "Cleanup + mulch + flowers + minor sod patches.", Decimal("795"))]),

    ("handyman",
     "Selah Handyman Services",
     "Inspection-list fix-ups, fast.",
     "Inspection Repair Punch List",
     "Targeted repair work from a buyer's inspection list. Most punch lists completed in one or two visits.",
     [("basic", "Up to 4 Items", "Single visit.", Decimal("295")),
      ("standard", "Up to 10 Items", "Single visit, parts included.", Decimal("595")),
      ("premium", "Full Punch List", "Multi-visit, parts + materials.", Decimal("1295"))]),

    ("website-design",
     "Cherry Lane Studio",
     "Modern realtor websites that convert.",
     "Realtor Website Build",
     "Modern Next.js or webflow site for solo agents and small teams. SEO baseline, mobile-first, Calendly-integrated.",
     [("basic", "Single-Page Site", "1 page + lead form.", Decimal("795")),
      ("standard", "Standard Site", "5 pages + blog + lead form.", Decimal("1995")),
      ("premium", "Premium Site", "10 pages + blog + listings widget + IDX.", Decimal("4495"))]),

    ("social-media",
     "Lower Valley Social Co.",
     "Done-for-you social for realtors.",
     "Realtor Social Management",
     "Monthly social media management — content, posting, engagement, monthly reporting.",
     [("basic", "1 Channel", "12 posts/mo on one platform.", Decimal("445")),
      ("standard", "2 Channels", "20 posts/mo on two platforms.", Decimal("795")),
      ("premium", "Full Social", "30 posts/mo on three platforms + reels.", Decimal("1295"))]),

    ("ai-agents",
     "Valley AI Studio",
     "Custom AI agents for realtor workflows.",
     "Custom AI Agent Build",
     "Custom-built AI agents for lead intake, pre-qualification, listing description generation, and CRM workflows.",
     [("basic", "Single Agent", "One agent + light integration.", Decimal("995")),
      ("standard", "Workflow Pack", "Three agents + CRM integration.", Decimal("2495")),
      ("premium", "Full Stack", "Five agents + CRM + analytics.", Decimal("4995"))]),

    ("automation",
     "Cascade Automations",
     "n8n + Zapier automations for realtor teams.",
     "Workflow Automation Build",
     "End-to-end workflow automation using n8n. Lead routing, follow-up sequences, document automation.",
     [("basic", "Single Flow", "One workflow, deployed.", Decimal("445")),
      ("standard", "Workflow Stack", "Three workflows + monitoring.", Decimal("1245")),
      ("premium", "Full Automation", "Five workflows + custom dashboards.", Decimal("2495"))]),

    ("crm-setup",
     "RealtorOps Studio",
     "Follow-Up Boss + KvCore + Sierra setup specialists.",
     "CRM Setup & Migration",
     "Full CRM setup from scratch or migration from another platform. Tag taxonomy, automation rules, smart lists.",
     [("basic", "Initial Setup", "Up to 500 contacts.", Decimal("445")),
      ("standard", "Migration + Setup", "Up to 2500 contacts.", Decimal("995")),
      ("premium", "Full Stack", "Full CRM + automations + dashboard.", Decimal("2495"))]),

    ("title-services",
     "Yakima Valley Title Company",
     "Local title services with concierge closings.",
     "Title & Closing Services",
     "Full-service title insurance and closing. Owner's policy, lender's policy, settlement services.",
     [("basic", "Standard Closing", "Standard residential.", Decimal("495")),
      ("standard", "Enhanced Closing", "Standard + enhanced owner policy.", Decimal("795")),
      ("premium", "Concierge Closing", "Mobile notary + enhanced policy + rush.", Decimal("1295"))]),

    ("inspection",
     "Cascade Home Inspections",
     "Thorough, plain-English inspection reports.",
     "Residential Home Inspection",
     "Full residential inspection with same-day plain-English report. Sewer scope, radon, mold add-ons available.",
     [("basic", "Up to 1500 sqft", "Standard report, 24h delivery.", Decimal("345")),
      ("standard", "Up to 3000 sqft", "Standard report, 24h delivery.", Decimal("445")),
      ("premium", "Over 3000 sqft", "Standard + sewer scope + thermal.", Decimal("795"))]),

    ("survey",
     "Sun Valley Land Surveying",
     "Boundary, topo, and lot-line surveys.",
     "Property Boundary Survey",
     "Licensed surveyor produces a recorded boundary survey. Fast turnaround in metro Yakima.",
     [("basic", "Pinpoint Only", "4 corners marked, no recorded survey.", Decimal("445")),
      ("standard", "Full Survey", "Recorded boundary survey.", Decimal("995")),
      ("premium", "Full + Topo", "Boundary + topographic + recorded.", Decimal("1995"))]),

    ("physical-staging",
     "Heritage Home Staging",
     "Physical staging for residential listings.",
     "Vacant Home Staging",
     "Full physical staging of vacant residential listings. Inventory + delivery + setup + 60-day rental.",
     [("basic", "Living + Dining", "Two-room stage.", Decimal("1295")),
      ("standard", "Whole Main Floor", "Up to 4 rooms.", Decimal("2495")),
      ("premium", "Whole Home", "Up to 8 rooms.", Decimal("3995"))]),

    ("decluttering-consultation",
     "Yakima Home Edit",
     "On-site decluttering and pre-listing prep.",
     "Decluttering Consultation",
     "On-site walkthrough with prioritized action plan. Optional hands-on assistance available.",
     [("basic", "Walkthrough Only", "60-minute walkthrough + plan.", Decimal("145")),
      ("standard", "Walkthrough + Plan", "Walkthrough + written plan + vendor referrals.", Decimal("245")),
      ("premium", "Full Service", "Walkthrough + 4 hours hands-on assist.", Decimal("595"))]),
]


EXTRA_BUNDLES = [
    {
        "vendor_email":   "skyline-aerials@yakimaweb.local",
        "name":           "Aerial Listing Pack",
        "description":    "Per-listing drone hero pack with two reshoots and unlimited revisions.",
        "price":          Decimal("475"),
        "cadence":        BillingCadence.ONE_TIME,
        "min_term":       1,
        "items":          [("Drone Photo & Video Pack", 1, "Drone hero + cinematic reel + unlimited revisions.")],
    },
    {
        "vendor_email":   "lower-valley-social@yakimaweb.local",
        "name":           "Realtor Social Quarterly",
        "description":    "Three months of full social management with monthly reporting and quarterly strategy.",
        "price":          Decimal("2295"),
        "cadence":        BillingCadence.QUARTERLY,
        "min_term":       3,
        "items":          [("Realtor Social Management", 3, "30 posts/mo on three platforms + monthly reporting.")],
    },
    {
        "vendor_email":   "valley-ai-studio@yakimaweb.local",
        "name":           "Realtor AI Stack",
        "description":    "Annual AI tooling subscription — agents, CRM integration, monthly reviews.",
        "price":          Decimal("8995"),
        "cadence":        BillingCadence.ANNUAL,
        "min_term":       12,
        "items":          [("Custom AI Agent Build", 1, "5 agents + CRM + monthly reviews.")],
    },
    {
        "vendor_email":   "cascade-automations@yakimaweb.local",
        "name":           "Workflow Retainer",
        "description":    "Monthly retainer for ongoing automation maintenance + new flow builds.",
        "price":          Decimal("995"),
        "cadence":        BillingCadence.MONTHLY,
        "min_term":       3,
        "items":          [("Workflow Automation Build", 1, "Up to 2 new workflows/mo + monitoring.")],
    },
    {
        "vendor_email":   "heritage-home-staging@yakimaweb.local",
        "name":           "Quarterly Stage Pack",
        "description":    "Pre-priced staging for the agent who lists three or more vacant homes per quarter.",
        "price":          Decimal("6495"),
        "cadence":        BillingCadence.QUARTERLY,
        "min_term":       3,
        "items":          [("Vacant Home Staging", 3, "Up to 3 listings/qtr, 60-day stage each.")],
    },
]


def _email_for(business: str) -> str:
    return slugify(business) + "@yakimaweb.local"


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
            "slug":          slugify(business)[:200],
            "status":        VendorProfile.Status.ACTIVE,
            "tagline":       tagline,
        },
    )
    return profile


def _ensure_buyer_pool(n: int) -> list[User]:
    pool: list[User] = []
    for i in range(n):
        email = f"demo-buyer-{i+1}@yakimaweb.local"
        user, created = User.objects.get_or_create(
            email=email,
            defaults={"full_name": f"Demo Buyer {i+1}", "role": "member"},
        )
        if created:
            user.set_unusable_password()
            user.save(update_fields=["password"])
        pool.append(user)
    return pool


REVIEW_TEMPLATES = [
    (5, "Professional, on-time, made my listing look great. Booking again next month."),
    (5, "Communication was excellent. Delivered ahead of schedule."),
    (5, "Quality matched the price. Will recommend to other agents."),
    (4, "Good work overall. One minor revision request, handled quickly."),
    (4, "Solid result. Pricing was fair for the quality delivered."),
    (5, "Best vendor in this category I have worked with. Booked them for three more listings."),
    (4, "Slightly slower than promised but the end product was excellent."),
    (5, "Trusted them with a difficult shoot — totally worth it."),
    (3, "Result was acceptable but felt expensive for what we got."),
    (5, "Made the inspection process painless. Buyer's agent loved them too."),
]


class Command(BaseCommand):
    help = "Extended marketplace seed: more vendors, services, packages, bundles, leads, reviews."

    def handle(self, *args, **opts):
        if not Category.objects.exists():
            self.stdout.write(self.style.ERROR(
                "No categories — run `seed_categories` first."
            ))
            return

        random.seed(20260504)
        now = timezone.now()
        services_by_email: dict[str, Service] = {}
        s_created = p_created = 0

        for cat_slug, business, tagline, svc_title, svc_desc, packages in EXTRA_VENDORS:
            email = _email_for(business)
            user = _ensure_user(email, business)
            vendor = _ensure_vendor(user, business, tagline)
            category = Category.objects.filter(slug=cat_slug).first()
            if category is None:
                continue

            service, was_created = Service.objects.get_or_create(
                vendor=vendor,
                title=svc_title,
                defaults={
                    "category":          category,
                    "description":       svc_desc,
                    "moderation_status": "approved",
                    "moderated_at":      now,
                },
            )
            if was_created:
                s_created += 1
            services_by_email[email] = service

            for tier, name, desc, price in packages:
                _, was = Package.objects.get_or_create(
                    service=service,
                    tier=tier,
                    defaults={
                        "name":          name,
                        "description":   desc,
                        "price_low":     price,
                        "price_high":    price,
                        "delivery_days": 5 if tier == PackageTier.BASIC else (7 if tier == PackageTier.STANDARD else 10),
                        "revisions":     1 if tier == PackageTier.BASIC else (2 if tier == PackageTier.STANDARD else 3),
                        "features":      [],
                    },
                )
                if was:
                    p_created += 1

        b_created = 0
        for spec in EXTRA_BUNDLES:
            email = spec["vendor_email"]
            service = services_by_email.get(email)
            if service is None:
                continue
            bundle, was_created = Bundle.objects.get_or_create(
                vendor=service.vendor,
                name=spec["name"],
                defaults={
                    "description":      spec["description"],
                    "price_total":      spec["price"],
                    "billing_cadence":  spec["cadence"],
                    "min_term_months":  spec["min_term"],
                    "moderation_status": "approved",
                    "moderated_at":     now,
                },
            )
            if was_created:
                b_created += 1
                for svc_title, qty, note in spec["items"]:
                    item_service = (
                        Service.objects.filter(title=svc_title, vendor=service.vendor).first()
                        or service
                    )
                    BundleItem.objects.get_or_create(
                        bundle=bundle,
                        service=item_service,
                        defaults={
                            "quantity_per_period": qty,
                            "fulfillment_note":    note,
                        },
                    )

        buyers = _ensure_buyer_pool(20)
        all_services = list(Service.objects.all())
        l_created = r_created = 0

        for service in all_services:
            buyers_for_vendor = random.sample(buyers, k=random.randint(2, 6))
            for buyer in buyers_for_vendor:
                if Lead.objects.filter(buyer=buyer, vendor=service.vendor, service=service).exists():
                    continue
                status = random.choices(
                    [LeadStatus.PENDING, LeadStatus.CONTACTED, LeadStatus.WON, LeadStatus.LOST],
                    weights=[3, 2, 4, 1],
                )[0]
                lead = Lead.objects.create(
                    vendor=service.vendor,
                    buyer=buyer,
                    service=service,
                    message=f"Interested in {service.title}. Available timeline?",
                    status=status,
                    won_at=now - timedelta(days=random.randint(7, 90)) if status == LeadStatus.WON else None,
                    lost_at=now - timedelta(days=random.randint(7, 90)) if status == LeadStatus.LOST else None,
                )
                l_created += 1

                if status == LeadStatus.WON and random.random() < 0.85:
                    rating, body = random.choice(REVIEW_TEMPLATES)
                    Review.objects.get_or_create(
                        lead=lead,
                        defaults={
                            "rating":            rating,
                            "body":              body,
                            "moderation_status": "approved",
                            "moderated_at":      now,
                        },
                    )
                    r_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Marketplace extras: services={s_created}, packages={p_created}, "
            f"bundles={b_created}, leads={l_created}, reviews={r_created}."
        ))
