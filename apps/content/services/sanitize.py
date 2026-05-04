"""Markdown → safe HTML pipeline using bleach + markdown."""
import bleach
import markdown as md

ALLOWED_TAGS = [
    "h2", "h3", "h4", "p", "br", "strong", "em", "u", "blockquote",
    "ul", "ol", "li", "a", "img", "code", "pre", "hr",
]
ALLOWED_ATTRS = {
    "a": ["href", "title", "rel"],
    "img": ["src", "alt", "title", "loading"],
}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]


def render_markdown(text: str) -> str:
    """Markdown → sanitized HTML."""
    raw = md.markdown(text, extensions=["fenced_code", "smarty", "tables"])
    return bleach.clean(
        raw,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
