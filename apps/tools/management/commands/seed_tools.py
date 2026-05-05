"""Seed the Tool registry. Idempotent."""

from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.tools.models import Tool

TOOLS = [
    {
        "slug": "description-writer",
        "name": "AI Listing Description Writer",
        "description": (
            "Turn a few facts about a property into MLS-ready listing copy. "
            "Compliant tone, no Fair-Housing pitfalls, ~30s per run."
        ),
        "model_id": "gemini-2.5-pro",
        "is_enabled": True,
        "cost_per_run_estimate_usd": Decimal("0.0150"),
        "member_daily_limit": 10,
        "realtor_daily_limit": 100,
    },
    {
        "slug": "furniture-remover",
        "name": "Empty-Room Photo Tool",
        "description": (
            "Upload a furnished room photo; receive an empty-room version "
            "ready for staging mockups. Two-step Gemini pipeline."
        ),
        "model_id": "gemini-2.5-flash-image",
        "is_enabled": True,
        "cost_per_run_estimate_usd": Decimal("0.0400"),
        "member_daily_limit": 5,
        "realtor_daily_limit": 50,
    },
    {
        "slug": "image-compressor",
        "name": "Lossless Image Compressor",
        "description": (
            "Shrink listing photos without losing a pixel of quality. "
            "JPG, PNG, WebP, HEIC, TIFF, GIF, BMP supported."
        ),
        "model_id": "local:pillow",
        "is_enabled": True,
        "cost_per_run_estimate_usd": Decimal("0.0000"),
        "member_daily_limit": 30,
        "realtor_daily_limit": 300,
    },
    {
        "slug": "flyer-generator",
        "name": "Realtor Flyer Generator",
        "description": (
            "Pick a design preset, paint your property facts, get a "
            "print-ready PDF flyer in about a minute."
        ),
        "model_id": "claude-opus-4-7",
        "is_enabled": True,
        "cost_per_run_estimate_usd": Decimal("0.0000"),
        "member_daily_limit": 3,
        "realtor_daily_limit": 20,
    },
]


class Command(BaseCommand):
    help = "Seed the Tool registry. Idempotent."

    def handle(self, *args, **opts):
        created = 0
        updated = 0
        for spec in TOOLS:
            tool, was_created = Tool.objects.get_or_create(
                slug=spec["slug"],
                defaults={k: v for k, v in spec.items() if k != "slug"},
            )
            if was_created:
                created += 1
                continue
            changed = False
            for k, v in spec.items():
                if k == "slug":
                    continue
                if getattr(tool, k) != v:
                    setattr(tool, k, v)
                    changed = True
            if changed:
                tool.save()
                updated += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Tools seeded: created={created}, updated={updated}, total={Tool.objects.count()}."
            )
        )
