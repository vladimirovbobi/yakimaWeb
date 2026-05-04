"""RSS / Atom feed helpers.

Per-author Atom feed for realtor blog posts. Uses django.contrib.syndication.
"""
from django.contrib.auth import get_user_model
from django.utils.text import slugify


User = get_user_model()


def author_slug(user) -> str:
    """Stable, URL-safe slug for an author. Combines the email-localpart + id."""
    base = (user.full_name or user.email).split("@", 1)[0]
    return f"{slugify(base)[:48]}-{user.pk}"


def find_author_by_slug(slug: str):
    """Resolve `<localpart>-<pk>` slug back to a user. Returns None if missing."""
    if "-" not in slug:
        return None
    pk = slug.rsplit("-", 1)[-1]
    if not pk.isdigit():
        return None
    return User.objects.filter(pk=int(pk)).first()
