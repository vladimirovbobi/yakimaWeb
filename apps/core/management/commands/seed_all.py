"""One-shot wrapper: runs all seed commands in order. Idempotent."""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management import call_command
from django.core.management.base import BaseCommand

SEEDS = [
    ("seed_categories",            "Categories"),
    ("seed_flairs",                "Forum flairs"),
    ("seed_brokerages",            "Brokerages"),
    ("seed_action_templates",      "Moderation action templates"),
    ("seed_tools",                 "AI tool registry"),
    ("seed_demo",                  "Demo content (base)"),
    ("seed_demo_marketplace",      "Demo marketplace (base)"),
    ("seed_demo_extras",           "Extended posts + threads + comments + replies"),
    ("seed_demo_marketplace_extras", "Extended vendors + bundles + leads + reviews"),
]


def _heal_post_images() -> int:
    from apps.content.models import Post

    placeholder_dir = Path(settings.BASE_DIR) / "frontend" / "public" / "img" / "posts"
    healed = 0
    for idx, post in enumerate(
        Post.objects.filter(hero_image="").order_by("id")
    ):
        n = (idx % 10) + 1
        src = placeholder_dir / f"post-{n}.jpg"
        if not src.exists():
            continue
        with src.open("rb") as fh:
            post.hero_image.save(src.name, File(fh), save=True)
        healed += 1
    return healed


def _heal_service_images() -> int:
    from apps.marketplace.models import Service

    placeholder_dir = (
        Path(settings.BASE_DIR) / "frontend" / "public" / "img" / "services"
    )
    healed = 0
    for idx, service in enumerate(
        Service.objects.filter(hero_image="").order_by("id")
    ):
        n = (idx % 12) + 1
        src = placeholder_dir / f"service-{n}.jpg"
        if not src.exists():
            continue
        with src.open("rb") as fh:
            service.hero_image.save(src.name, File(fh), save=True)
        healed += 1
    return healed


class Command(BaseCommand):
    help = "Run all seed commands in order. Idempotent."

    def handle(self, *args, **opts):
        for name, label in SEEDS:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n→ {label} ({name})"))
            try:
                call_command(name)
            except Exception as e:  # noqa: BLE001
                self.stdout.write(self.style.ERROR(f"  failed: {e}"))

        # Heal pre-existing rows missing images. Re-running seed_all
        # backfills placeholder photos onto every Post + Service that
        # was created before the placeholder pipeline existed.
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n→ Healing missing post/service images"
        ))
        try:
            posts_healed = _heal_post_images()
            services_healed = _heal_service_images()
            self.stdout.write(self.style.SUCCESS(
                f"  posts={posts_healed}, services={services_healed}"
            ))
        except Exception as e:  # noqa: BLE001
            self.stdout.write(self.style.ERROR(f"  heal failed: {e}"))

        self.stdout.write(self.style.SUCCESS("\nseed_all done."))
