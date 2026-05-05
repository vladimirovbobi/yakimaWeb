"""Resolve social URLs to embeddable metadata. No 3rd-party JS — server-side only."""
import re
from dataclasses import dataclass

YT_PATTERNS = [
    re.compile(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|shorts/|embed/))([\w-]{11})"),
]
IG_PATTERN = re.compile(r"instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)")


@dataclass
class ResolvedEmbed:
    provider: str
    kind: str
    external_id: str
    canonical_url: str
    embed_html: str
    thumb_url: str = ""
    title: str = ""


def resolve(url: str) -> ResolvedEmbed | None:
    """Detect provider + return ResolvedEmbed. No network call (privacy-first stub)."""
    url = url.strip()

    # YouTube
    for pat in YT_PATTERNS:
        m = pat.search(url)
        if m:
            vid = m.group(1)
            kind = "short" if "/shorts/" in url else "video"
            embed_url = f"https://www.youtube-nocookie.com/embed/{vid}"
            html = (
                f'<iframe src="{embed_url}" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" '
                f'allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
                f'allowfullscreen class="w-full h-full border-0"></iframe>'
            )
            thumb = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
            return ResolvedEmbed(
                provider="youtube", kind=kind, external_id=vid,
                canonical_url=f"https://www.youtube.com/watch?v={vid}",
                embed_html=html, thumb_url=thumb,
            )

    # Instagram
    m = IG_PATTERN.search(url)
    if m:
        sid = m.group(1)
        embed_url = f"https://www.instagram.com/p/{sid}/embed/"
        html = (
            f'<iframe src="{embed_url}" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" '
            f'class="w-full h-full border-0"></iframe>'
        )
        return ResolvedEmbed(
            provider="instagram", kind="post", external_id=sid,
            canonical_url=f"https://www.instagram.com/p/{sid}/",
            embed_html=html, thumb_url="",
        )

    return None
