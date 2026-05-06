"""Shared helpers for tasteful placeholder generation.

Pillow only. Hand-drawn-feeling line art on warm-dark backgrounds with gold
accents. Every image gets a tiny `[demo]` corner pip so it cannot be confused
with shipped art. Deterministic — same seed in, same noise out.
"""
from __future__ import annotations

import math
import random
from pathlib import Path
from typing import Iterable, Sequence

from PIL import Image, ImageDraw, ImageFilter, ImageFont


# ── Brand palette (cream — vrov-new 1301 inversion).
# Token names retained; values inverted so existing renderers paint dark
# strokes on cream surfaces. See docs/research/cream-palette-from-vrov-1301.md.
BLACK    = (245, 239, 224)  # page bg (was #080604)
DEEP     = (237, 229, 205)  # secondary surface
PANEL    = (229, 219, 188)  # cards
WARM     = (216, 201, 164)  # accent surface
GOLD     = (139, 115, 64)   # accent — darker for cream contrast
GOLD_HI  = (184, 152, 96)   # hover
GOLD_DIM = (90, 74, 40)     # unchanged — works on either bg
IVORY    = (26, 18, 8)      # primary text (was #F5EFE0)
MIST     = (90, 79, 66)     # secondary text


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_IMG = ROOT / "frontend" / "public" / "img"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = (
        ["DejaVuSerif-Bold.ttf"] if bold else ["DejaVuSerif.ttf"]
    ) + ["DejaVuSans.ttf"]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def base_canvas(w: int, h: int, *, seed: int = 0) -> Image.Image:
    """Warm-dark canvas with a soft off-center gold glow + faint grain."""
    img = Image.new("RGB", (w, h), DEEP)
    rng = random.Random(seed)

    # Glow
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    cx = int(w * (0.30 + 0.45 * rng.random()))
    cy = int(h * (0.25 + 0.50 * rng.random()))
    max_r = int(math.hypot(w, h) * 0.50)
    steps = 36
    for i in range(steps, 0, -1):
        r = int(max_r * (i / steps))
        a = int(70 * (1 - i / steps))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*WARM, a))
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=70))
    img.paste(overlay, (0, 0), overlay)

    # Vignette — uses GOLD_DIM on cream so corners read as warm shade, not harsh black
    vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)
    for i in range(8):
        a = int(8 * i)
        vd.rectangle((i * 4, i * 4, w - i * 4, h - i * 4),
                     outline=(*GOLD_DIM, a), width=2)
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=60))
    img.paste(vignette, (0, 0), vignette)

    # Subtle grain — toned to cream contrast (lower alpha than dark variant)
    grain = Image.new("L", (w, h))
    gp = grain.load()
    for y in range(h):
        for x in range(w):
            gp[x, y] = rng.randint(0, 8)
    g_rgba = Image.merge("RGBA", (grain, grain, grain, grain.point(lambda p: p // 4)))
    img.paste(g_rgba, (0, 0), g_rgba)

    return img


def stroke(img: Image.Image, points: Sequence[tuple[float, float]],
           color=GOLD, width: int = 2, alpha: int = 200) -> None:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    pts = [(int(x), int(y)) for x, y in points]
    if len(pts) >= 2:
        d.line(pts, fill=(*color, alpha), width=width)
    img.paste(overlay, (0, 0), overlay)


def line(img: Image.Image, p1: tuple[float, float], p2: tuple[float, float],
         color=GOLD, width: int = 2, alpha: int = 200) -> None:
    stroke(img, [p1, p2], color=color, width=width, alpha=alpha)


def thin_grid(img: Image.Image, cols: int = 12, rows: int = 0,
              color=GOLD_DIM, alpha: int = 22) -> None:
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(1, cols):
        x = int(w * i / cols)
        d.line([(x, 0), (x, h)], fill=(*color, alpha), width=1)
    if rows:
        for j in range(1, rows):
            y = int(h * j / rows)
            d.line([(0, y), (w, y)], fill=(*color, alpha), width=1)
    img.paste(overlay, (0, 0), overlay)


def diagonal_strokes(img: Image.Image, *, density: int = 4) -> None:
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for i in range(density):
        offset = int(w * (0.18 + 0.16 * i))
        a = max(15, 80 - i * 12)
        d.line(
            [(offset, 0), (offset + h, h)],
            fill=(*GOLD, a),
            width=1 if i > 0 else 2,
        )
    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=0.5))
    img.paste(overlay, (0, 0), overlay)


def ring(img: Image.Image, cx: int, cy: int, r: int,
         color=GOLD, width: int = 2, alpha: int = 200) -> None:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.ellipse((cx - r, cy - r, cx + r, cy + r),
              outline=(*color, alpha), width=width)
    img.paste(overlay, (0, 0), overlay)


def filled_circle(img: Image.Image, cx: int, cy: int, r: int,
                  color=GOLD, alpha: int = 220) -> None:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*color, alpha))
    img.paste(overlay, (0, 0), overlay)


def watermark(img: Image.Image, label: str = "demo") -> None:
    """Tiny [demo] pip in the lower-right corner. Always present."""
    w, h = img.size
    pip_size = max(11, int(min(w, h) * 0.014))
    f = font(pip_size, bold=False)
    text = f"[{label}]"
    d = ImageDraw.Draw(img, "RGBA")
    bbox = d.textbbox((0, 0), text, font=f)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad = max(4, int(pip_size * 0.5))
    margin = max(8, int(pip_size * 0.9))
    x0 = w - margin - tw - pad * 2
    y0 = h - margin - th - pad * 2
    x1 = w - margin
    y1 = h - margin
    # Dark pip on cream — IVORY is now the dark text token; pip reads strongly.
    d.rectangle((x0, y0, x1, y1), fill=(*IVORY, 200), outline=(*GOLD_DIM, 220))
    d.text((x0 + pad, y0 + pad - 2), text, font=f, fill=(*GOLD_HI, 240))


def save_jpeg(img: Image.Image, path: Path, quality: int = 86) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="JPEG", quality=quality, optimize=True, progressive=True)
    print(f"Wrote: {path}")


def label_corner(img: Image.Image, eyebrow: str, *, color=GOLD) -> None:
    """Tiny eyebrow label in the upper-left."""
    w, h = img.size
    d = ImageDraw.Draw(img, "RGBA")
    pad_x = max(20, int(w * 0.04))
    pad_y = max(20, int(h * 0.06))
    f = font(max(11, int(min(w, h) * 0.018)), bold=True)
    d.text((pad_x, pad_y), eyebrow.upper(), font=f, fill=color)
    d.line(
        [(pad_x, pad_y + 22), (pad_x + 30, pad_y + 22)],
        fill=color,
        width=1,
    )


def deterministic(seed: str | int) -> random.Random:
    return random.Random(hash(str(seed)) & 0xFFFFFFFF)


def all_motifs() -> Iterable[str]:  # docs / discovery only
    return ()
