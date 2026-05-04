"""Markdown → safe HTML pipeline using bleach + markdown.

Also exposes `sanitize_html` for raw HTML inputs (TipTap rich-text editor).

Allowlist sized for TipTap output: paragraphs, h2/h3/h4, lists, blockquote,
code/pre, inline marks, links, images. Anchors are auto-tagged with
`rel="noopener nofollow ugc"` to avoid SEO leakage from UGC.
"""
import bleach

import markdown as md

ALLOWED_TAGS = [
    "p", "br", "hr",
    "h2", "h3", "h4",
    "ul", "ol", "li",
    "blockquote",
    "code", "pre",
    "strong", "em", "b", "i", "u",
    "a", "img",
]
ALLOWED_ATTRS = {
    "a": ["href", "title", "rel", "target"],
    "img": ["src", "alt", "title", "loading"],
}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]
LINK_REL = "noopener nofollow ugc"


def _link_attrs(attrs: dict, new: bool = False) -> dict:  # noqa: ARG001
    """bleach.linkify-style attribute filter — force `rel` on anchors.

    Used as a post-clean linker so internal/external links get
    `rel="noopener nofollow ugc"` and external links open safely.
    """
    href = attrs.get((None, "href"), "") or ""
    if href:
        attrs[(None, "rel")] = LINK_REL
        if href.startswith(("http://", "https://")):
            attrs[(None, "target")] = "_blank"
    return attrs


def _attr_filter(tag: str, name: str, value: str) -> bool:
    """Allowlist attributes per-tag. Forces `rel` on `<a>` to LINK_REL."""
    allowed = ALLOWED_ATTRS.get(tag, [])
    if name not in allowed:
        return False
    if tag == "a" and name == "rel":
        # Accept anything; we rewrite via linkify after clean.
        return True
    return True


def _sanitize(html: str) -> str:
    cleaned = bleach.clean(
        html or "",
        tags=ALLOWED_TAGS,
        attributes=_attr_filter,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
    # Rewrite anchor `rel`/`target` regardless of input.
    return bleach.linkify(cleaned, callbacks=[_link_attrs], skip_tags=["pre", "code"])


def render_markdown(text: str) -> str:
    """Markdown → sanitized HTML."""
    raw = md.markdown(text, extensions=["fenced_code", "smarty", "tables"])
    return _sanitize(raw)


def sanitize_html(html: str) -> str:
    """Sanitize raw HTML (e.g. from TipTap) using the same allowlist."""
    return _sanitize(html)


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
