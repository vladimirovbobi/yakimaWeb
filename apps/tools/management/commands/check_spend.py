"""Print today's Gemini spend + remaining budget."""
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.tools.services.spend_cap import (
    get_today_spend_usd,
    remaining_budget_usd,
)


class Command(BaseCommand):
    help = "Print today's Gemini spend + remaining budget."

    def handle(self, *args, **options):
        cap = float(getattr(settings, "GEMINI_DAILY_SPEND_CAP_USD", 0) or 0)
        spent = get_today_spend_usd()
        remaining = remaining_budget_usd()
        self.stdout.write(f"Daily cap:    ${cap:.2f}")
        self.stdout.write(f"Spent today:  ${spent:.2f}")
        if remaining == float("inf"):
            self.stdout.write("Remaining:    unbounded (no cap configured)")
        else:
            self.stdout.write(f"Remaining:    ${remaining:.2f}")
