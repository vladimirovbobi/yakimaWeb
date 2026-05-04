"""Generate hero placeholder images for the homepage and sub-pages.

Pure gradient + stroke compositions. No AI photos. Each image gets a tiny
"[demo]" corner pip so it's never confused with final art.

Required deps: Pillow.

Output: frontend/public/img/hero/
    hero-home.jpg       (1920x1080)
    hero-blog.jpg       (1920x600)
    hero-services.jpg   (1920x600)
    hero-community.jpg  (1920x600)
    hero-tools.jpg      (1920x600)

Runtime: ~3s. Run via `make assets` or directly:

    python scripts/generate_hero_placeholders.py
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "public" / "img" / "hero"

BLACK = (8, 6, 4)
DEEP = (13, 9, 4)
PANEL = (20, 16, 8)
WARM = (26, 18, 8)
GOLD = (191, 160, 106)
GOLD_HI = (222, 201, 138)
GOLD_DIM = (90, 74, 40)
IVORY = (245, 239, 224)
MIST = (206, 196, 168)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        ["DejaVuSerif-Bold.ttf"] if bold else ["DejaVuSerif.ttf"]
    ) + ["DejaVuSans.ttf"]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _radial_gradient(w: int, h: int, *, cx_ratio: float = 0.7,
                     cy_ratio: float = 0.4) -> Image.Image:
    """Black base with a soft warm glow off-center."""
    img = Image.new("RGB", (w, h), BLACK)
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    cx, cy = int(w * cx_ratio), int(h * cy_ratio)
    max_r = int(math.hypot(w, h) * 0.55)
    steps = 40
    for i in range(steps, 0, -1):
        r = int(max_r * (i / steps))
        # Warm gold glow fading out
        a = int(60 * (1 - i / steps))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*WARM, a))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=80))
    img.paste(overlay, (0, 0), overlay)
    return img


def _gold_strokes(img: Image.Image, *, density: int = 4) -> None:
    """Thin diagonal gold accent strokes."""
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(density):
        offset = int(w * (0.15 + 0.18 * i))
        alpha = 90 if i == 0 else 50 - i * 8
        alpha = max(15, alpha)
        d.line(
            [(offset, 0), (offset + h, h)],
            fill=(*GOLD, alpha),
            width=1 if i > 0 else 2,
        )
    # One brighter accent
    d.line(
        [(int(w * 0.78), 0), (int(w * 0.78) + h, h)],
        fill=(*GOLD_HI, 140),
        width=2,
    )
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=0.6))
    img.paste(overlay, (0, 0), overlay)


def _grid(img: Image.Image) -> None:
    """Faint vertical grid lines for architectural feel."""
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    cols = 12
    for i in range(1, cols):
        x = int(w * i / cols)
        d.line([(x, 0), (x, h)], fill=(*GOLD_DIM, 24), width=1)
    img.paste(overlay, (0, 0), overlay)


def _label_pip(img: Image.Image, label: str) -> None:
    """Tiny [demo] + section-label pip in the bottom-right."""
    d = ImageDraw.Draw(img, "RGBA")
    f = _font(18, bold=True)
    text = f"[demo]  ·  {label}"
    bbox = d.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad = 10
    margin = 28
    w, h = img.size
    rect = (
        w - margin - tw - pad * 2,
        h - margin - th - pad * 2,
        w - margin,
        h - margin,
    )
    d.rectangle(rect, fill=(*BLACK, 200), outline=GOLD)
    d.text((rect[0] + pad, rect[1] + pad - 2), text, font=f, fill=GOLD_HI)


def _section_label(img: Image.Image, eyebrow: str, title: str) -> None:
    """Tasteful eyebrow + serif title in the upper-left."""
    d = ImageDraw.Draw(img)
    w, h = img.size
    pad_x = max(48, int(w * 0.06))
    pad_y = max(48, int(h * 0.18))

    eyebrow_font = _font(22, bold=True)
    d.text((pad_x, pad_y), eyebrow, font=eyebrow_font, fill=GOLD)
    d.line(
        [(pad_x, pad_y + 38), (pad_x + 80, pad_y + 38)],
        fill=GOLD,
        width=2,
    )

    title_font = _font(int(h * 0.10), bold=True)
    d.text((pad_x, pad_y + 64), title, font=title_font, fill=IVORY)


def _render(w: int, h: int, eyebrow: str, title: str, label: str) -> Image.Image:
    img = _radial_gradient(w, h)
    _grid(img)
    _gold_strokes(img)
    _section_label(img, eyebrow, title)
    _label_pip(img, label)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    targets = [
        ("hero-home.jpg",      1920, 1080, "YAKIMA WEB",
         "Central Washington, on the record.", "home"),
        ("hero-blog.jpg",      1920, 600,  "INSIGHTS",
         "Realtor Notes", "blog"),
        ("hero-services.jpg",  1920, 600,  "MARKETPLACE",
         "Local Services", "services"),
        ("hero-community.jpg", 1920, 600,  "COMMUNITY",
         "Forum", "community"),
        ("hero-tools.jpg",     1920, 600,  "AI TOOLS",
         "Listing Toolkit", "tools"),
    ]
    for filename, w, h, eyebrow, title, label in targets:
        img = _render(w, h, eyebrow, title, label)
        path = OUT / filename
        img.save(path, format="JPEG", quality=84, optimize=True, progressive=True)
        print(f"Wrote: {path}")


if __name__ == "__main__":
    main()
