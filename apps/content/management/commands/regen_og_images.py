"""Regenerate OG images for all Posts.

NOTE: `Post` does not yet have an `og_image` ImageField. Files are written to
`MEDIA_ROOT/og/post-<id>.png` (or to S3 under the same path when USE_S3=True).
A subsequent migration should add `og_image = ImageField(upload_to='og/')` to
`apps.content.models.Post` so `Post.og_image_url` can render directly.
"""
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from apps.content.models import Post, PostType
from apps.content.services.og_image import render


VARIANT_BY_POST_TYPE = {
    PostType.ORG:     "default",
    PostType.BLOG:    "blog",
    PostType.LANDING: "default",
}


class Command(BaseCommand):
    help = "Regenerate OG images for every Post into MEDIA_ROOT/og/."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true",
                            help="Regenerate even if file exists.")

    def handle(self, *args, **opts):
        force = opts["force"]
        rendered = 0
        skipped  = 0

        for post in Post.objects.all().iterator():
            relpath = f"og/post-{post.pk}.png"

            if not force and default_storage.exists(relpath):
                skipped += 1
                continue

            buf = render(
                title=post.title,
                subtitle=post.excerpt or "",
                variant=VARIANT_BY_POST_TYPE.get(post.post_type, "default"),
            )

            if default_storage.exists(relpath):
                default_storage.delete(relpath)
            default_storage.save(relpath, buf)
            rendered += 1

        if not getattr(settings, "USE_S3", False):
            local = Path(settings.MEDIA_ROOT) / "og"
            local.mkdir(parents=True, exist_ok=True)

        self.stdout.write(self.style.SUCCESS(
            f"OG images: rendered={rendered}, skipped={skipped}."
        ))
