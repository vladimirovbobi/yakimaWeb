"""1200x630 OG image generator.

Pillow-based. Deterministic — same input yields same output.

Fonts: tries Cormorant Garamond + Raleway under STATIC_ROOT/fonts. If absent,
falls back to Pillow's bundled DejaVu. Run `manage.py download_og_fonts` to
fetch the brand fonts (TODO Phase 2.1) — until then, fallback is acceptable.
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Literal

from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger(__name__)

# Brand tokens (mirror tailwind config)
BG_TOP    = (8, 6, 4)
BG_BOTTOM = (13, 9, 4)
GOLD      = (191, 160, 106)
GOLD_HI   = (222, 201, 138)
IVORY     = (245, 239, 224)
MIST      = (206, 196, 168)

WIDTH  = 1200
HEIGHT = 630
PADDING = 64

EYEBROW_BY_VARIANT: dict[str, str] = {
    "default":     "INSIGHTS",
    "blog":        "BLOG",
    "forum":       "COMMUNITY",
    "marketplace": "MARKETPLACE",
}

Variant = Literal["default", "blog", "forum", "marketplace"]

FONTS_DIR = Path(settings.BASE_DIR) / "static" / "fonts"


def _load_font(candidates: list[str], size: int) -> ImageFont.ImageFont:
    for name in candidates:
        path = FONTS_DIR / name
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    try:
        return ImageFont.truetype("DejaVuSerif.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _serif(size: int) -> ImageFont.ImageFont:
    return _load_font(
        ["CormorantGaramond-SemiBold.ttf", "CormorantGaramond-Regular.ttf"], size,
    )


def _sans(size: int) -> ImageFont.ImageFont:
    return _load_font(
        ["Raleway-Medium.ttf", "Raleway-Regular.ttf"], size,
    )


def _gradient_bg() -> Image.Image:
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_TOP)
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        t = y / max(1, HEIGHT - 1)
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
    return img


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int,
          max_lines: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if (bbox[2] - bbox[0]) > max_width and current:
            lines.append(current)
            current = word
            if len(lines) >= max_lines:
                break
        else:
            current = candidate
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and len(words) > sum(len(l.split()) for l in lines):
        last = lines[-1]
        while last and draw.textbbox((0, 0), last + "…", font=font)[2] > max_width:
            last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
        lines[-1] = last + "…"
    return lines


def _draw_tracked(draw: ImageDraw.ImageDraw, xy, text, font, fill, *,
                  tracking_em: float = 0.22) -> None:
    x, y = xy
    bbox = draw.textbbox((0, 0), "M", font=font)
    em = bbox[2] - bbox[0]
    extra = int(em * tracking_em)
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        cb = draw.textbbox((0, 0), ch, font=font)
        x += (cb[2] - cb[0]) + extra


def render(title: str, subtitle: str = "", variant: Variant = "default") -> io.BytesIO:
    """Return PNG BytesIO for a 1200x630 OG card."""
    img = _gradient_bg()
    draw = ImageDraw.Draw(img)

    # Brand mark (top-left)
    brand_font = _serif(36)
    draw.text((PADDING, PADDING), "Yakima Web", font=brand_font, fill=GOLD)

    # Eyebrow (top-right)
    eyebrow = EYEBROW_BY_VARIANT.get(variant, "INSIGHTS")
    eyebrow_font = _sans(20)
    eyebrow_bbox = draw.textbbox((0, 0), eyebrow, font=eyebrow_font)
    eyebrow_w = (eyebrow_bbox[2] - eyebrow_bbox[0]) + int(
        (eyebrow_bbox[2] - eyebrow_bbox[0]) * 0.22,
    )
    _draw_tracked(
        draw, (WIDTH - PADDING - eyebrow_w, PADDING + 12), eyebrow,
        eyebrow_font, MIST,
    )

    # Title
    title_font = _serif(72)
    title_lines = _wrap(draw, title, title_font, WIDTH - 2 * PADDING, 3)
    title_y = 200
    for line in title_lines:
        draw.text((PADDING, title_y), line, font=title_font, fill=GOLD_HI)
        bbox = draw.textbbox((0, 0), line, font=title_font)
        title_y += (bbox[3] - bbox[1]) + 12

    # Subtitle
    if subtitle:
        sub_font = _sans(28)
        sub_lines = _wrap(draw, subtitle, sub_font, WIDTH - 2 * PADDING, 2)
        sub_y = title_y + 24
        for line in sub_lines:
            draw.text((PADDING, sub_y), line, font=sub_font, fill=MIST)
            bbox = draw.textbbox((0, 0), line, font=sub_font)
            sub_y += (bbox[3] - bbox[1]) + 8

    # Footer
    footer_font = _sans(22)
    draw.text(
        (PADDING, HEIGHT - PADDING - 28),
        "yakimaweb.com",
        font=footer_font, fill=IVORY,
    )

    rule_y = HEIGHT - PADDING - 48
    draw.line([(PADDING, rule_y), (PADDING + 80, rule_y)], fill=GOLD, width=2)

    out = io.BytesIO()
    img.save(out, format="PNG", optimize=True)
    out.seek(0)
    return out
