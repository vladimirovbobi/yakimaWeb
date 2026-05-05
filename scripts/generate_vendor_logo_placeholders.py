"""Generate 8 unique 600x600 JPEGs for vendor logo placeholders.

Same monogram grammar as avatars but bigger / more presence. Tasteful.

Output: frontend/public/img/vendors/vendor-logo-{1..8}.jpg
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import ImageDraw, Image

from _placeholder_common import (
    BLACK, GOLD, GOLD_DIM, GOLD_HI, MIST, PUBLIC_IMG, WARM,
    base_canvas, filled_circle, line, ring, save_jpeg, stroke, watermark,
)


W, H = 600, 600
OUT = PUBLIC_IMG / "vendors"


def _frame(img):
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((20, 20, W - 20, H - 20),
                outline=(*GOLD_DIM, 160), width=2)
    d.rectangle((36, 36, W - 36, H - 36),
                outline=(*GOLD, 200), width=1)


def m_arc(img):
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(img, "RGBA")
    d.pieslice((cx - 200, cy - 200, cx + 200, cy + 200),
               start=210, end=330, outline=(*GOLD, 240), width=4)
    line(img, (cx - 180, cy + 100), (cx + 180, cy + 100),
         color=GOLD_HI, width=3, alpha=240)


def m_keystone(img):
    cx, cy = W // 2, H // 2 - 20
    pts = [(cx - 130, cy + 110),
           (cx - 80, cy - 110),
           (cx + 80, cy - 110),
           (cx + 130, cy + 110),
           (cx - 130, cy + 110)]
    stroke(img, pts, color=GOLD, width=3, alpha=240)
    inner = [(cx - 80, cy + 50),
             (cx - 50, cy - 60),
             (cx + 50, cy - 60),
             (cx + 80, cy + 50),
             (cx - 80, cy + 50)]
    stroke(img, inner, color=GOLD_HI, width=2, alpha=220)
    line(img, (cx - 200, cy + 110), (cx + 200, cy + 110),
         color=GOLD_DIM, width=2, alpha=220)


def m_compass(img):
    cx, cy = W // 2, H // 2
    ring(img, cx, cy, 200, color=GOLD, width=3, alpha=240)
    ring(img, cx, cy, 170, color=GOLD_DIM, width=1, alpha=200)
    for k in range(8):
        a = k / 8 * math.tau - math.pi / 2
        x1 = cx + int(math.cos(a) * 170)
        y1 = cy + int(math.sin(a) * 170)
        x2 = cx + int(math.cos(a) * 200)
        y2 = cy + int(math.sin(a) * 200)
        line(img, (x1, y1), (x2, y2), color=GOLD, width=2, alpha=220)
    # N arrow
    pts = [(cx, cy - 140),
           (cx + 18, cy + 0),
           (cx, cy - 30),
           (cx - 18, cy + 0),
           (cx, cy - 140)]
    stroke(img, pts, color=GOLD_HI, width=3, alpha=240)


def m_grid_emblem(img):
    cx, cy = W // 2, H // 2
    cell = 60
    for r in range(-2, 3):
        for c in range(-2, 3):
            x = cx + c * cell
            y = cy + r * cell
            ring(img, x, y, 18, color=GOLD if (r + c) % 2 == 0 else GOLD_DIM,
                 width=2, alpha=200)
    ring(img, cx, cy, 50, color=GOLD_HI, width=3, alpha=240)


def m_double_ring(img):
    cx, cy = W // 2, H // 2
    ring(img, cx - 50, cy, 130, color=GOLD, width=3, alpha=240)
    ring(img, cx + 50, cy, 130, color=GOLD_HI, width=3, alpha=240)
    line(img, (cx - 200, cy + 160), (cx + 200, cy + 160),
         color=GOLD_DIM, width=2, alpha=200)


def m_mountain_emblem(img):
    cx, cy = W // 2, H // 2
    pts = [(cx - 200, cy + 110),
           (cx - 60, cy - 80),
           (cx + 20, cy + 30),
           (cx + 100, cy - 110),
           (cx + 200, cy + 110),
           (cx - 200, cy + 110)]
    stroke(img, pts, color=GOLD, width=3, alpha=240)
    line(img, (cx - 200, cy + 110), (cx + 200, cy + 110),
         color=GOLD_DIM, width=2, alpha=220)
    ring(img, cx, cy + 110, 18, color=GOLD_HI, width=2, alpha=240)


def m_river_glyph(img):
    cx, cy = W // 2, H // 2
    pts = [(cx - 220, cy - 60)]
    for i in range(1, 12):
        t = i / 11
        x = cx - 220 + int(440 * t)
        y = cy - 60 + int(math.sin(t * math.pi * 1.5) * 100)
        pts.append((x, y))
    stroke(img, pts, color=GOLD, width=4, alpha=240)
    pts2 = [(p[0], p[1] + 40) for p in pts]
    stroke(img, pts2, color=GOLD_HI, width=2, alpha=200)


def m_orchard_emblem(img):
    cx, cy = W // 2, H // 2
    for k in range(7):
        a = k / 7 * math.tau - math.pi / 2
        x = cx + int(math.cos(a) * 120)
        y = cy + int(math.sin(a) * 120)
        ring(img, x, y, 28, color=GOLD, width=2, alpha=220)
    ring(img, cx, cy, 60, color=GOLD_HI, width=3, alpha=240)
    filled_circle(img, cx, cy, 10, color=GOLD, alpha=240)


MOTIFS = [
    m_arc,
    m_keystone,
    m_compass,
    m_grid_emblem,
    m_double_ring,
    m_mountain_emblem,
    m_river_glyph,
    m_orchard_emblem,
]


def render(idx: int, motif) -> Image.Image:
    img = base_canvas(W, H, seed=idx * 277 + 41)
    _frame(img)
    motif(img)
    watermark(img)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for idx, motif in enumerate(MOTIFS, start=1):
        img = render(idx, motif)
        save_jpeg(img, OUT / f"vendor-logo-{idx}.jpg")


if __name__ == "__main__":
    main()
