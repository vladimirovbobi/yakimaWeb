"""Generate 8 unique 256x256 JPEGs for user avatar placeholders.

Abstract geometric monograms — circle bisected, triangle stack, two-tone
wedge, etc. NOT initials. Tasteful gold-on-warm.

Output: frontend/public/img/avatars/avatar-{1..8}.jpg
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import ImageDraw, Image

from _placeholder_common import (
    BLACK, DEEP, GOLD, GOLD_DIM, GOLD_HI, MIST, PUBLIC_IMG, WARM,
    base_canvas, filled_circle, line, ring, save_jpeg, stroke, watermark,
)


W, H = 256, 256
OUT = PUBLIC_IMG / "avatars"


def _frame(img):
    """Round-feel inset frame."""
    d = ImageDraw.Draw(img, "RGBA")
    inset = 8
    d.ellipse((inset, inset, W - inset, H - inset),
              outline=(*GOLD_DIM, 140), width=1)
    d.ellipse((inset + 6, inset + 6, W - inset - 6, H - inset - 6),
              outline=(*GOLD, 200), width=2)


# ── 8 monograms ─────────────────────────────────────────────────────────────


def m_split_circle(img):
    cx, cy = W // 2, H // 2
    filled_circle(img, cx, cy, 70, color=GOLD, alpha=220)
    d = ImageDraw.Draw(img, "RGBA")
    # Cover left half with warm
    d.pieslice((cx - 70, cy - 70, cx + 70, cy + 70),
               start=90, end=270, fill=(*WARM, 255))
    ring(img, cx, cy, 70, color=GOLD_HI, width=2, alpha=240)


def m_triangle_stack(img):
    cx, cy = W // 2, H // 2
    for i, a in enumerate((0.95, 0.62, 0.35)):
        size = int(80 * a)
        pts = [
            (cx, cy - size),
            (cx - size, cy + size // 2),
            (cx + size, cy + size // 2),
            (cx, cy - size),
        ]
        col = (GOLD, GOLD_HI, GOLD_DIM)[i]
        stroke(img, pts, color=col, width=2, alpha=210)


def m_wedge(img):
    cx, cy = W // 2, H // 2
    r = 72
    d = ImageDraw.Draw(img, "RGBA")
    d.pieslice((cx - r, cy - r, cx + r, cy + r),
               start=210, end=330, fill=(*GOLD, 230))
    d.pieslice((cx - r, cy - r, cx + r, cy + r),
               start=30, end=150, outline=(*GOLD_HI, 240), width=3)
    ring(img, cx, cy, r, color=GOLD_DIM, width=2, alpha=180)


def m_chevron(img):
    cx, cy = W // 2, H // 2
    for i in range(3):
        off = 28 + i * 12
        pts = [(cx - 70, cy + off + 30),
               (cx, cy + off - 20),
               (cx + 70, cy + off + 30)]
        col = GOLD_HI if i == 0 else (GOLD if i == 1 else GOLD_DIM)
        stroke(img, pts, color=col, width=3, alpha=220)


def m_dot_constellation(img):
    cx, cy = W // 2, H // 2
    nodes = []
    for k in range(5):
        ang = k / 5 * math.tau - math.pi / 2
        x = cx + int(math.cos(ang) * 70)
        y = cy + int(math.sin(ang) * 70)
        nodes.append((x, y))
    for i, a in enumerate(nodes):
        b = nodes[(i + 2) % len(nodes)]
        line(img, a, b, color=GOLD_DIM, width=1, alpha=180)
    for n in nodes:
        filled_circle(img, n[0], n[1], 8, color=GOLD, alpha=240)
    filled_circle(img, cx, cy, 5, color=GOLD_HI, alpha=240)


def m_concentric(img):
    cx, cy = W // 2, H // 2
    for r, col, w, a in (
        (78, GOLD,     2, 220),
        (60, GOLD_DIM, 1, 200),
        (42, GOLD_HI,  2, 240),
        (24, GOLD,     1, 180),
    ):
        ring(img, cx, cy, r, color=col, width=w, alpha=a)
    filled_circle(img, cx, cy, 8, color=GOLD_HI, alpha=240)


def m_bars(img):
    cx, cy = W // 2, H // 2
    bars = (40, 64, 52, 78, 36)
    for i, h in enumerate(bars):
        x = cx - 56 + i * 24
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle((x, cy + 70 - h, x + 16, cy + 70),
                    outline=(*GOLD, 220), width=2)
    line(img, (cx - 80, cy + 70), (cx + 80, cy + 70),
         color=GOLD_DIM, width=1, alpha=200)


def m_diamond(img):
    cx, cy = W // 2, H // 2
    pts = [(cx, cy - 80), (cx + 60, cy), (cx, cy + 80), (cx - 60, cy), (cx, cy - 80)]
    stroke(img, pts, color=GOLD, width=3, alpha=240)
    inner = [(cx, cy - 40), (cx + 30, cy), (cx, cy + 40), (cx - 30, cy), (cx, cy - 40)]
    stroke(img, inner, color=GOLD_HI, width=2, alpha=240)
    filled_circle(img, cx, cy, 6, color=GOLD, alpha=240)


MOTIFS = [
    m_split_circle,
    m_triangle_stack,
    m_wedge,
    m_chevron,
    m_dot_constellation,
    m_concentric,
    m_bars,
    m_diamond,
]


def render(idx: int, motif) -> Image.Image:
    img = base_canvas(W, H, seed=idx * 311 + 7)
    _frame(img)
    motif(img)
    watermark(img)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for idx, motif in enumerate(MOTIFS, start=1):
        img = render(idx, motif)
        save_jpeg(img, OUT / f"avatar-{idx}.jpg")


if __name__ == "__main__":
    main()
