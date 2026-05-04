"""Seed marketplace category tree (treebeard MP_Node). Idempotent."""
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.marketplace.models import Category


TREE: dict[str, list[str]] = {
    "Photography": [
        "Real Estate Photography", "Drone Photography",
        "Twilight Photography", "3D Tour",
    ],
    "Lending": [
        "Conventional", "FHA", "VA", "Construction", "Refinance",
    ],
    "Service": [
        "Junk Removal", "Cleaning", "Painting", "Landscaping", "Handyman",
    ],
    "Marketing": [
        "Website Design", "Social Media", "Branding", "Print Materials",
    ],
    "Tech": [
        "AI Agents", "Automation", "CRM Setup", "Lead Capture",
    ],
    "Legal & Closing": [
        "Title Services", "Closing Services", "Inspection", "Survey",
    ],
    "Staging": [
        "Physical Staging", "Virtual Staging", "Decluttering Consultation",
    ],
    "Other": [],
}


class Command(BaseCommand):
    help = "Seed marketplace categories. Idempotent."

    def handle(self, *args, **opts):
        created = 0
        existed = 0
        for top_label, children in TREE.items():
            top_slug = slugify(top_label)
            top = Category.objects.filter(slug=top_slug).first()
            if top is None:
                top = Category.add_root(slug=top_slug, label=top_label)
                created += 1
            else:
                existed += 1
            for child_label in children:
                child_slug = slugify(child_label)
                if Category.objects.filter(slug=child_slug).exists():
                    existed += 1
                    continue
                top.add_child(slug=child_slug, label=child_label)
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f"Created {created} categories. {existed} already existed."
        ))
