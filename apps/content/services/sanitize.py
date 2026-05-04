"""Markdown → safe HTML pipeline using bleach + markdown.

Also exposes `sanitize_html` for raw HTML inputs (TipTap rich-text editor).
"""
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


def sanitize_html(html: str) -> str:
    """Sanitize raw HTML (e.g. from TipTap) using the same allowlist."""
    return bleach.clean(
        html or "",
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )


def render_post_body(text: str) -> str:
    """Render body to HTML.

    If `<p>` or `<h2>` markers are present we treat input as raw HTML (TipTap)
    and just sanitize. Otherwise treat as Markdown for backwards compat.
    """
    if not text:
        return ""
    needle_html = ("<p>" in text) or ("<h2" in text) or ("<h3" in text)
    if needle_html:
        return sanitize_html(text)
    return render_markdown(text)
