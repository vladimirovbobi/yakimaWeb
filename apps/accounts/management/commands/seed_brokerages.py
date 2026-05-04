"""Seed WA brokerages.

TODO: There is no `Brokerage` model in apps/accounts/models.py yet. The
`RealtorProfile.brokerage` field is currently a free-text CharField. When
a `Brokerage` model is introduced (likely Phase 2 hardening), this command
will import the starter list below.

Until then, this command exits with a notice. The seed list is preserved
inline so the data survives until the model lands.
"""
from django.apps import apps
from django.core.management.base import BaseCommand


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
    help = "Seed WA brokerages — currently a no-op until Brokerage model lands."

    def handle(self, *args, **opts):
        try:
            apps.get_model("accounts", "Brokerage")
        except LookupError:
            self.stdout.write(self.style.WARNING(
                "No `Brokerage` model in apps.accounts. Skipping seed.\n"
                f"Starter list preserved in this command file ({len(BROKERAGES)} entries)."
            ))
            return

        Brokerage = apps.get_model("accounts", "Brokerage")
        created = 0
        existed = 0
        for name, city in BROKERAGES:
            _, was_created = Brokerage.objects.get_or_create(
                name=name, defaults={"city": city},
            )
            if was_created:
                created += 1
            else:
                existed += 1
        self.stdout.write(self.style.SUCCESS(
            f"Brokerages: created={created}, existed={existed}."
        ))
