"""Seed demo content. Idempotent. Content created with moderation_status=approved."""
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.accounts.models import (LicenseType, RealtorProfile,
                                   VerificationStatus)
from apps.content.models import (Post, PostStatus, PostType, SocialEmbed,
                                  SocialKind, SocialProvider)
from apps.forum.models import Flair, ForumThread


User = get_user_model()


# Placeholder JPGs ship with the frontend; we copy them into Django storage
# so the API returns a valid hero_image URL on every seeded post.
PLACEHOLDER_DIR = Path(settings.BASE_DIR) / "frontend" / "public" / "img" / "posts"


def _attach_placeholder(post: Post, idx: int) -> None:
    """Deterministically assign post-{N}.jpg to a Post instance."""
    if post.hero_image:
        return
    n = (idx % 10) + 1
    src = PLACEHOLDER_DIR / f"post-{n}.jpg"
    if not src.exists():
        return
    with src.open("rb") as fh:
        post.hero_image.save(src.name, File(fh), save=True)

DEMO_REALTOR_EMAIL = "demo-realtor@yakimaweb.local"


ORG_POSTS = [
    {
        "title": "What the Yakima Valley housing market did this quarter",
        "excerpt": "A grounded look at sale prices, days on market, and inventory across Yakima, Selah, and the Lower Valley.",
        "body": (
            "## The headline\n\n"
            "Median sale prices in the Yakima Valley held within a narrow band this quarter, "
            "but the story underneath the median is more useful than the median itself. "
            "Inventory crept up. Days on market stretched. The buyers who showed up came with "
            "tighter pre-approvals and were less willing to compete on appraisal gaps.\n\n"
            "## What the numbers say\n\n"
            "Single-family detached homes in central Yakima cleared at a median that was nearly "
            "flat year over year. The median time from list to mutual acceptance climbed by a "
            "double-digit percentage. New listings outpaced pendings for the first time since the "
            "post-pandemic correction. Selah and West Valley saw faster movement at the lower end "
            "of the price band; the Lower Valley showed more patience among sellers willing to "
            "wait for the right offer.\n\n"
            "## What changed under the surface\n\n"
            "Three things matter more than the median right now. First, conventional buyers are "
            "back in the mix at sub-7% rates and they are negotiating differently than the cash "
            "buyers who dominated the last cycle. Second, FHA and VA appraisal sensitivity is "
            "back, and that is reshaping how listings are priced into the bracket caps. Third, "
            "out-of-area buyers are still looking at the Valley, but the wave is smaller and "
            "more selective than two years ago.\n\n"
            "## What we tell our buyers\n\n"
            "Slow down. Make appraisal-protected offers. Walk every property twice. Ask for "
            "seller concessions toward a rate buydown rather than a price reduction; the math "
            "almost always works in your favor in this rate environment.\n\n"
            "## What we tell our sellers\n\n"
            "Price into the bracket where buyers actually qualify. Stage sparingly. Photograph "
            "well. Be patient on offer night and let the second-best offer compete itself into "
            "first place. Concessions are negotiable; principal is not.\n"
        ),
    },
    {
        "title": "5 questions every Yakima buyer should ask before bidding",
        "excerpt": "A short, plain checklist that has saved our clients real money. Print it. Ask the questions out loud.",
        "body": (
            "Buying a home in the Yakima Valley should feel like a careful decision, not a "
            "panic. The five questions below are the ones we ask on every single transaction. "
            "They are simple. They surface real risks. Skip any of them and you are betting on "
            "luck.\n\n"
            "### 1. What does the seller actually owe?\n\n"
            "Public records show liens. Liens that exceed the home's market value mean the "
            "seller cannot close at your offer price. You can still buy the house, but you and "
            "your agent need to know up front whether you are negotiating with the seller or "
            "with the seller's bank.\n\n"
            "### 2. What is the appraisal risk on this listing?\n\n"
            "If your loan is FHA, VA, or USDA, your appraisal will be tighter than a "
            "conventional appraisal. Ask your agent to pull the last two comparable closings "
            "within a half-mile and check whether the list price is supported by them.\n\n"
            "### 3. What does the seller disclosure actually say?\n\n"
            "In Washington, sellers must complete a Form 17 disclosure. Read every line. Pay "
            "particular attention to the moisture, drainage, septic, and well sections. Ask the "
            "listing agent to clarify any 'don't know' answers in writing.\n\n"
            "### 4. What is the property tax trajectory?\n\n"
            "Yakima County reassesses on a cycle. A home that was assessed before recent "
            "improvements may carry a tax bill that no longer reflects market value. Pull the "
            "last three years of assessments and ask your lender to forecast year-one and "
            "year-two payments.\n\n"
            "### 5. What is the realistic insurance picture?\n\n"
            "Wildfire and wildland-urban-interface risk is real in the Valley. Get a quote "
            "before you finalize your offer, not after. A surprise insurance non-renewal is one "
            "of the worst ways to learn that your dream home is in a high-risk zone.\n"
        ),
    },
    {
        "title": "How we verify every realtor on this platform",
        "excerpt": "ARELLO checks, brokerage attestation, and a public audit trail. Why we do it the long way.",
        "body": (
            "## Why this matters\n\n"
            "Every realtor profile on Yakima Web carries a verified badge, a license number, an "
            "expiration date, and a brokerage. None of that is on the honor system. Here is how "
            "the pipeline works and why we built it.\n\n"
            "## The ARELLO check\n\n"
            "Washington's Department of Licensing does not publish a public real-time API for "
            "license status, so we use ARELLO, the multi-jurisdiction regulator-backed "
            "verification service. When a realtor signs up, our system makes a live call to "
            "ARELLO with the license number and the surname on file. We persist the raw response "
            "in our audit table, including the queried timestamp.\n\n"
            "## What we do with the response\n\n"
            "ARELLO returns one of seven status codes. We map them to internal statuses: "
            "`ACTIVE` becomes `verified`. `INACTIVE` and `EXPIRED` become `expired`. "
            "`SUSPENDED` and `REVOKED` become exactly what they say. `NOT_FOUND` produces an "
            "explicit unmatched profile and the realtor cannot post until the issue is "
            "resolved. Edge cases like `SURRENDERED` map to revoked.\n\n"
            "## The recurring check\n\n"
            "ARELLO state changes. Brokers move firms, surrender licenses, or get suspended. "
            "Once a month, our scheduler re-checks every active realtor profile and updates the "
            "internal status if anything changed. Anyone whose license has lapsed loses posting "
            "privileges automatically; we never wait for a complaint.\n\n"
            "## The audit trail\n\n"
            "Every check writes a row that we never delete. Auditors and platform members can "
            "inspect the verification timeline for any realtor profile. We believe the cost of "
            "a heavier compliance footprint is worth it for the trust this gives buyers, "
            "sellers, and the realtors themselves.\n"
        ),
    },
]


REALTOR_BLOG_TOPICS = [
    {
        "title": "Selah neighborhood guide",
        "excerpt": "Schools, parks, and which streets to walk before you buy.",
        "body": (
            "Selah punches above its weight on livability. The schools are well-rated, the "
            "downtown is walkable in a way that surprises out-of-area buyers, and the price "
            "per square foot still trails Yakima proper by a meaningful margin.\n\n"
            "Walk Wenas Avenue between First and Sixth. Drive the river loop on a weekday "
            "morning before you commit. The neighborhoods south of the freeway and the older "
            "blocks east of First trade quickly when they list — the supply is genuinely "
            "thin.\n\n"
            "If you have school-age kids, pull the assessment data on each of the three "
            "elementary catchments. They are not interchangeable.\n"
        ),
    },
    {
        "title": "When to lower your price",
        "excerpt": "A clear rule of thumb based on showings, traffic, and time on market.",
        "body": (
            "If you have been on the market for fourteen days with strong showing traffic "
            "and zero offers, your price is the problem. If you have low showing traffic, "
            "your photos and your description are the problem. The two diagnoses are very "
            "different and they have different fixes.\n\n"
            "A price reduction within the first three weeks recovers nearly all of its "
            "potential value. A price reduction at week eight signals desperation and "
            "buyers will price that into their offers.\n\n"
            "If you are going to reduce, reduce decisively. A $5,000 reduction on a "
            "$450,000 listing is invisible to the algorithm and invisible to your saved "
            "search subscribers.\n"
        ),
    },
    {
        "title": "Should you remodel before selling?",
        "excerpt": "Almost never. Here are the three exceptions.",
        "body": (
            "The honest answer is almost always no. Most sellers who remodel before listing "
            "recover less than the cost of the remodel and absorb three to six months of "
            "carrying costs they did not need to absorb.\n\n"
            "There are three exceptions. First, kitchens with original-condition cabinets, "
            "vinyl floors, and laminate counters in homes priced over the local median — a "
            "$15,000 cosmetic refresh routinely returns more than its cost on offer night. "
            "Second, homes with a clearly failed primary bathroom — buyers walk through a "
            "bad primary and never come back. Third, homes with curb appeal so weak that "
            "showing volume is suppressed before anyone walks inside.\n\n"
            "Everything else, leave for the buyer to imagine.\n"
        ),
    },
    {
        "title": "Cash-out refinance basics",
        "excerpt": "How it works, when it makes sense, and what to ask your lender.",
        "body": (
            "A cash-out refinance replaces your current mortgage with a larger one and "
            "delivers the difference to you in cash, less closing costs. It is one of the "
            "cheapest forms of borrowing available to homeowners with equity, and one of "
            "the most dangerous if you misuse it.\n\n"
            "It makes sense when the cash funds something that builds long-term value: a "
            "home improvement that you would have financed at a higher rate, a student-loan "
            "consolidation that materially reduces your blended interest rate, or a one-time "
            "emergency. It does not make sense to fund consumption or speculation.\n\n"
            "Ask your lender for the all-in APR, not just the note rate. Ask for the "
            "break-even month — the month when your monthly savings exceed your closing "
            "costs. If you do not plan to stay in the home past the break-even, do not do "
            "the deal.\n"
        ),
    },
    {
        "title": "Drone photos: are they worth it?",
        "excerpt": "Yes, but only on the listings where they actually show something.",
        "body": (
            "Drone photography is worth it on roughly one-third of the listings we represent. "
            "On a quarter-acre lot in central Yakima with no notable view and no special "
            "lot features, a drone photo adds nothing your standard exterior shot did not "
            "already convey.\n\n"
            "On listings with acreage, a notable orchard, river or canal frontage, or a "
            "property layout that is hard to read at ground level, a single well-composed "
            "drone photo often becomes the listing's hero image and meaningfully outperforms "
            "ground-level photography in click-through rate.\n\n"
            "Hire someone who knows the difference. A bad drone photo is worse than no drone "
            "photo at all.\n"
        ),
    },
]


FORUM_THREADS = [
    ("question",   "Best inspector for older homes in central Yakima?",
     "Closing on a 1948 home next month. Looking for an inspector who actually understands "
     "knob-and-tube, plaster walls, and the kind of foundation issues you see in pre-war "
     "Pacific Northwest construction. Recommendations welcome."),
    ("discussion", "Has the cash-buyer wave actually slowed?",
     "Anecdotally I am seeing fewer cash offers on listings under $450K. Curious whether "
     "anyone else is seeing the same thing or whether it is just my pipeline."),
    ("help",       "FHA appraisal came in low — what now?",
     "Listed at $379K, FHA appraisal came back at $362K. Buyer cannot bring the gap. "
     "Looking for advice on whether to negotiate, relist conventional, or hold."),
    ("market",     "Why are Selah listings sitting longer than last year?",
     "Anyone with hard numbers? My anecdotal read is that the median DOM in Selah is up "
     "noticeably, but I do not have access to the segmented data."),
    ("local-news", "Yakima County reassessment letters going out this month",
     "Heads up to anyone who closed in the last 18 months — your reassessment is probably "
     "in the mail. Worth opening immediately and worth checking against your appeal "
     "deadlines."),
    ("show-tell",  "Twilight shoot from last weekend",
     "Wanted to share a drone twilight shot from a 1.2-acre listing in West Valley. The "
     "orchard frontage is the whole story for this property. Comments welcome."),
    ("question",   "Recommendations for a junk-removal vendor — full estate?",
     "Estate sale clean-out next month. Three-bedroom, two-car garage, plus an outbuilding. "
     "Anyone with a vendor they trust for full clean-outs?"),
    ("discussion", "Are virtual staging photos still worth it?",
     "Buyers seem to have gotten more sophisticated about spotting virtual staging. Curious "
     "whether anyone has seen a meaningful click-through difference between virtual and "
     "physical staging in the last six months."),
    ("off-topic",  "Best coffee in downtown Yakima for a 7am client meeting?",
     "Working on building a regular Friday-morning client touch-base. Anyone with a quiet "
     "downtown spot that opens at 7?"),
    ("help",       "Buyer wants to write a love letter — should I let them?",
     "Buyer is set on writing a personal letter to the seller. I have explained the fair "
     "housing risks. Looking for the cleanest way to redirect this energy into something "
     "that actually helps their offer."),
]


SOCIAL_EMBEDS = [
    {
        "external_id": "dQw4w9WgXcQ",
        "title": "Yakima market quarterly recap",
        "description": "Short walkthrough of the latest quarter's numbers.",
        "canonical_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    },
    {
        "external_id": "9bZkp7q19f0",
        "title": "Selah neighborhood drone tour",
        "description": "A two-minute aerial tour of Selah's residential core.",
        "canonical_url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
    },
    {
        "external_id": "kJQP7kiw5Fk",
        "title": "How we verify realtors",
        "description": "ARELLO checks, brokerage attestation, audit trail.",
        "canonical_url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
    },
]


def _get_org_author() -> User:
    return (
        User.objects.filter(is_superuser=True).first()
        or User.objects.filter(is_staff=True).first()
        or User.objects.first()
    )


def _get_or_create_demo_realtor() -> User:
    user, created = User.objects.get_or_create(
        email=DEMO_REALTOR_EMAIL,
        defaults={"full_name": "Demo Realtor", "is_realtor": True, "role": "realtor"},
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    RealtorProfile.objects.get_or_create(
        user=user,
        defaults={
            "license_number": "DEMO-12345",
            "license_type": LicenseType.BROKER,
            "verification_status": VerificationStatus.VERIFIED,
            "verified_at": timezone.now(),
            "brokerage": "Demo Brokerage of Yakima",
            "bio": "Seeded demo realtor. Used for staging content only.",
        },
    )
    return user


class Command(BaseCommand):
    help = "Seed demo posts, blogs, threads, and social embeds. Idempotent."

    def handle(self, *args, **opts):
        org_author = _get_org_author()
        if org_author is None:
            self.stdout.write(self.style.ERROR(
                "No users in DB — create a superuser before running seed_demo."
            ))
            return

        demo_realtor = _get_or_create_demo_realtor()
        now = timezone.now()

        org_created = 0
        for idx, spec in enumerate(ORG_POSTS):
            slug = slugify(spec["title"])[:240]
            post, was_created = Post.objects.get_or_create(
                slug=slug,
                defaults={
                    "author": org_author,
                    "post_type": PostType.ORG,
                    "status": PostStatus.PUBLISHED,
                    "title": spec["title"],
                    "excerpt": spec["excerpt"],
                    "body": spec["body"],
                    "moderation_status": "approved",
                    "moderated_at": now,
                    "published_at": now,
                },
            )
            if was_created:
                org_created += 1
            _attach_placeholder(post, idx)

        blog_created = 0
        for idx, spec in enumerate(REALTOR_BLOG_TOPICS):
            slug = slugify(spec["title"])[:240]
            post, was_created = Post.objects.get_or_create(
                slug=slug,
                defaults={
                    "author": demo_realtor,
                    "post_type": PostType.BLOG,
                    "status": PostStatus.PUBLISHED,
                    "title": spec["title"],
                    "excerpt": spec["excerpt"],
                    "body": spec["body"],
                    "moderation_status": "approved",
                    "moderated_at": now,
                    "published_at": now,
                },
            )
            if was_created:
                blog_created += 1
            # Offset realtor posts by 5 so they don't share visuals with org posts.
            _attach_placeholder(post, idx + 5)

        thread_created = 0
        for flair_slug, title, body in FORUM_THREADS:
            flair = Flair.objects.filter(slug=flair_slug).first()
            if flair is None:
                continue
            if ForumThread.objects.filter(title=title).exists():
                continue
            ForumThread.objects.create(
                author=demo_realtor,
                flair=flair,
                title=title,
                body=body,
                moderation_status="approved",
                moderated_at=now,
            )
            thread_created += 1

        embed_created = 0
        for spec in SOCIAL_EMBEDS:
            _, was_created = SocialEmbed.objects.get_or_create(
                provider=SocialProvider.YOUTUBE,
                external_id=spec["external_id"],
                defaults={
                    "kind": SocialKind.VIDEO,
                    "title": spec["title"],
                    "description": spec["description"],
                    "canonical_url": spec["canonical_url"],
                    "thumb_url": f"https://img.youtube.com/vi/{spec['external_id']}/hqdefault.jpg",
                    "is_pinned": True,
                    "published_at": now,
                },
            )
            if was_created:
                embed_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Demo seed: org={org_created}, blogs={blog_created}, "
            f"threads={thread_created}, embeds={embed_created}."
        ))
