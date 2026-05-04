"""Read Vite manifest to resolve hashed asset URLs.

Usage in templates:
  {% load vite %}
  <link rel="stylesheet" href="{% vite_asset 'static/src/css/tailwind.css' %}">
  <script type="module" src="{% vite_asset 'static/src/js/main.js' %}"></script>
"""
import json
from functools import lru_cache
from pathlib import Path

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()

MANIFEST_PATH = Path(settings.BASE_DIR) / "static" / "dist" / ".vite" / "manifest.json"


@lru_cache(maxsize=1)
def _manifest() -> dict:
    if not MANIFEST_PATH.exists():
        return {}
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@register.simple_tag
def vite_asset(entry: str) -> str:
    """Resolve Vite manifest entry to its hashed static URL."""
    m = _manifest()
    rec = m.get(entry)
    if not rec:
        return static(entry)
    return static(rec.get("file", entry))


@register.simple_tag
def vite_css(entry: str) -> str:
    """Resolve CSS associated with a JS entry (Vite splits CSS into separate files)."""
    m = _manifest()
    rec = m.get(entry)
    if not rec or not rec.get("css"):
        return ""
    return static(rec["css"][0])
