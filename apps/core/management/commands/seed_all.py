"""One-shot wrapper: runs all seed commands in order. Idempotent."""
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


class Command(BaseCommand):
    help = "Run all seed commands in order. Idempotent."

    def handle(self, *args, **opts):
        for name, label in SEEDS:
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n→ {label} ({name})"))
            try:
                call_command(name)
            except Exception as e:  # noqa: BLE001
                self.stdout.write(self.style.ERROR(f"  failed: {e}"))
        self.stdout.write(self.style.SUCCESS("\nseed_all done."))
