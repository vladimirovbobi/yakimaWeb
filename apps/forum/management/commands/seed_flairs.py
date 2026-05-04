"""Seed forum flairs. Idempotent via slug."""
from django.core.management.base import BaseCommand

from apps.forum.models import Flair


FLAIRS = [
    ("question",   "Question",     "gold",     10),
    ("discussion", "Discussion",   "ivory",    20),
    ("help",       "Help Needed",  "warn",     30),
    ("local-news", "Local News",   "gold-hi",  40),
    ("market",     "Market Talk",  "gold",     50),
    ("show-tell",  "Show & Tell",  "mist",     60),
    ("off-topic",  "Off-Topic",    "dim",      70),
]


class Command(BaseCommand):
    help = "Seed forum flairs. Idempotent."

    def handle(self, *args, **opts):
        created = 0
        existed = 0
        for slug, label, color, sort in FLAIRS:
            _, was_created = Flair.objects.get_or_create(
                slug=slug,
                defaults={"label": label, "color": color, "sort_order": sort},
            )
            if was_created:
                created += 1
            else:
                existed += 1
        self.stdout.write(self.style.SUCCESS(
            f"Created {created} flairs. {existed} already existed."
        ))
