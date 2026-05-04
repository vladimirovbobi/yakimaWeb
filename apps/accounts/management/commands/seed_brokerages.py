"""Seed WA brokerages — populates the Brokerage table for FE autocomplete."""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.accounts.models import Brokerage


BROKERAGES: list[tuple[str, str]] = [
    ("Berkshire Hathaway HomeServices Central Washington Real Estate", "Yakima"),
    ("John L. Scott — Yakima",                                          "Yakima"),
    ("Heritage Moultray Real Estate",                                   "Yakima"),
    ("Coldwell Banker La Casa",                                          "Yakima"),
    ("Almon Commercial Real Estate",                                     "Yakima"),
    ("RE/MAX Yakima",                                                    "Yakima"),
    ("Windermere Real Estate — Yakima",                                  "Yakima"),
    ("Keller Williams Yakima Valley",                                    "Yakima"),
    ("Century 21 Lance Tate Realty",                                    "Yakima"),
    ("Yakima Realty",                                                    "Yakima"),
    ("Selah Real Estate Group",                                          "Selah"),
    ("Sundquist Real Estate",                                            "Selah"),
    ("Sunnyside Realty",                                                 "Sunnyside"),
    ("Cascade West Realty",                                              "Sunnyside"),
    ("Premier Real Estate of Sunnyside",                                 "Sunnyside"),
    ("Ellensburg Real Estate Pros",                                      "Ellensburg"),
    ("CBC The Property Manager",                                         "Ellensburg"),
    ("Coldwell Banker Lifestyle Properties",                             "Ellensburg"),
    ("Pacific Crest Real Estate",                                        "Ellensburg"),
    ("Tri-Cities Real Estate Network",                                   "Kennewick"),
]


class Command(BaseCommand):
    help = "Seed WA brokerages."

    def handle(self, *args, **opts):
        created = 0
        existed = 0
        for name, city in BROKERAGES:
            slug = slugify(name)[:200] or slugify(f"{name}-{city}")[:200]
            _, was_created = Brokerage.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "city": city, "state": "WA"},
            )
            if was_created:
                created += 1
            else:
                existed += 1
        self.stdout.write(self.style.SUCCESS(
            f"Brokerages: created={created}, existed={existed}."
        ))
