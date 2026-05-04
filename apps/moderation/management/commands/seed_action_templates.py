"""Seed default ActionTemplate rows. Idempotent — re-run safe."""
from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.moderation.models import ActionTemplate

TEMPLATES = [
    {
        "slug": "removed_spam",
        "label": "Removed - Spam",
        "action": "remove",
        "default_reason": "Removed: spam / promotional.",
        "sort_order": 10,
    },
    {
        "slug": "removed_harassment",
        "label": "Removed - Harassment",
        "action": "remove",
        "default_reason": "Removed: harassment / personal attack.",
        "sort_order": 20,
    },
    {
        "slug": "removed_off_topic",
        "label": "Removed - Off-topic",
        "action": "remove",
        "default_reason": "Removed: off-topic for this surface.",
        "sort_order": 30,
    },
    {
        "slug": "removed_doxxing",
        "label": "Removed - Doxxing",
        "action": "remove",
        "default_reason": "Removed: doxxing / personal information disclosure.",
        "sort_order": 40,
    },
    {
        "slug": "removed_promotional",
        "label": "Removed - Promotional",
        "action": "remove",
        "default_reason": "Removed: undisclosed promotional / unauthorized advertising.",
        "sort_order": 50,
    },
    {
        "slug": "approved_with_edit",
        "label": "Approved - With edit",
        "action": "approve",
        "default_reason": "Approved after edit by moderator.",
        "sort_order": 60,
    },
    {
        "slug": "approved_no_change",
        "label": "Approved - No change",
        "action": "approve",
        "default_reason": "Approved as-is; classifier flagged borderline content.",
        "sort_order": 70,
    },
]


class Command(BaseCommand):
    help = "Seed ActionTemplate rows for one-click moderator decisions."

    def handle(self, *args, **options):
        created = updated = 0
        for spec in TEMPLATES:
            obj, was_created = ActionTemplate.objects.update_or_create(
                slug=spec["slug"],
                defaults={
                    "label": spec["label"],
                    "action": spec["action"],
                    "default_reason": spec["default_reason"],
                    "sort_order": spec["sort_order"],
                    "is_active": True,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1
        self.stdout.write(self.style.SUCCESS(
            f"ActionTemplates seeded — created={created} updated={updated} "
            f"total={ActionTemplate.objects.count()}"
        ))
