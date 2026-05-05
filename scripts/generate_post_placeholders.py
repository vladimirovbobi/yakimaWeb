"""Generate 10 unique 1600x900 (16:9) JPEGs for blog post placeholders.

Hand-drawn-feeling line art on warm-dark backgrounds with gold accents.
Each motif is rooted in something Yakima Valley — wine rows, orchards,
the Cascades, riverside topology. Tasteful, low-density, no AI photo look.

Output: frontend/public/img/posts/post-{1..10}.jpg
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import ImageDraw, ImageFilter, Image

from _placeholder_common import (
    BLACK, DEEP, GOLD, GOLD_DIM, GOLD_HI, IVORY, MIST, PUBLIC_IMG, WARM,
    base_canvas, diagonal_strokes, filled_circle, font, label_corner, line,
    ring, save_jpeg, stroke, thin_grid, watermark,
)


W, H = 1600, 900
OUT = PUBLIC_IMG / "posts"


# ── Motif drawers ───────────────────────────────────────────────────────────

def m_arches(img):
    """Spanning arches — masonry / townhouse vibe."""
    base_y = int(H * 0.78)
    cols = 5
    span = W // cols
    for c in range(cols):
        cx = c * span + span // 2
        r = int(span * 0.46)
        ring(img, cx, base_y, r, color=GOLD, width=2, alpha=160)
        ring(img, cx, base_y, r - 8, color=GOLD_DIM, width=1, alpha=140)
        line(img, (cx - r, base_y), (cx - r, base_y + 220),
             color=GOLD_DIM, width=1, alpha=120)
        line(img, (cx + r, base_y), (cx + r, base_y + 220),
             color=GOLD_DIM, width=1, alpha=120)
    line(img, (0, base_y), (W, base_y), color=GOLD, width=1, alpha=180)


def m_staircase(img):
    """Architectural staircase abstract."""
    steps = 9
    sx = int(W * 0.14)
    sy = int(H * 0.74)
    sw = int(W * 0.50)
    sh = int(H * 0.48)
    step_w = sw // steps
    step_h = sh // steps
    for i in range(steps):
        x0 = sx + i * step_w
        y0 = sy - i * step_h
        line(img, (x0, y0), (x0 + step_w, y0),
             color=GOLD, width=2, alpha=160)
        line(img, (x0 + step_w, y0), (x0 + step_w, y0 - step_h),
             color=GOLD, width=2, alpha=160)
    line(img, (sx, sy), (sx + sw, sy - sh),
         color=GOLD_HI, width=1, alpha=200)


def m_window_grid(img):
    """A grid of tall windows — interior / loft feel."""
    cx = W // 2
    cy = H // 2
    cols, rows = 6, 3
    cw, ch = 140, 220
    gap_x, gap_y = 30, 28
    total_w = cols * cw + (cols - 1) * gap_x
    total_h = rows * ch + (rows - 1) * gap_y
    x0 = cx - total_w // 2
    y0 = cy - total_h // 2
    for r in range(rows):
        for c in range(cols):
            x = x0 + c * (cw + gap_x)
            y = y0 + r * (ch + gap_y)
            d = ImageDraw.Draw(img, "RGBA")
            d.rectangle((x, y, x + cw, y + ch),
                        outline=(*GOLD_DIM, 180), width=1)
            line(img, (x + cw // 2, y), (x + cw // 2, y + ch),
                 color=GOLD_DIM, width=1, alpha=120)
            line(img, (x, y + ch // 2), (x + cw, y + ch // 2),
                 color=GOLD_DIM, width=1, alpha=120)


def m_crosshatch(img):
    """Loose crosshatch field."""
    w, h = img.size
    for k in range(40):
        y = int(h * (0.2 + 0.6 * (k / 40)))
        line(img, (int(w * 0.10), y), (int(w * 0.50), y - 60),
             color=GOLD_DIM, width=1, alpha=80 + (k % 8) * 6)
    for k in range(40):
        y = int(h * (0.2 + 0.6 * (k / 40)))
        line(img, (int(w * 0.55), y - 60), (int(w * 0.92), y),
             color=GOLD_DIM, width=1, alpha=80 + (k % 8) * 6)


def m_vineyard_rows(img):
    """Yakima Valley vineyard rows in perspective."""
    horizon = int(H * 0.34)
    vp = (int(W * 0.55), horizon)
    rows = 14
    for i in range(rows):
        x_start = int(W * (-0.05 + 1.05 * i / rows))
        line(img, (x_start, H), vp, color=GOLD, width=1,
             alpha=110 + (i % 4) * 16)
    line(img, (0, horizon), (W, horizon),
         color=GOLD_HI, width=1, alpha=180)


def m_mountains(img):
    """Cascades silhouette."""
    horizon = int(H * 0.62)
    pts = [
        (0, horizon),
        (int(W * 0.10), int(H * 0.50)),
        (int(W * 0.18), int(H * 0.42)),
        (int(W * 0.27), int(H * 0.52)),
        (int(W * 0.38), int(H * 0.36)),
        (int(W * 0.50), int(H * 0.46)),
        (int(W * 0.60), int(H * 0.30)),
        (int(W * 0.72), int(H * 0.44)),
        (int(W * 0.84), int(H * 0.40)),
        (int(W * 0.94), int(H * 0.50)),
        (W, horizon),
    ]
    stroke(img, pts, color=GOLD, width=2, alpha=200)
    # Snow caps
    for i in (3, 5, 7):
        peak = pts[i]
        line(img, (peak[0] - 30, peak[1] + 22), peak,
             color=GOLD_HI, width=1, alpha=180)
        line(img, peak, (peak[0] + 30, peak[1] + 22),
             color=GOLD_HI, width=1, alpha=180)
    # Foreground rolling line
    fg = [(0, int(H * 0.78)),
          (int(W * 0.30), int(H * 0.74)),
          (int(W * 0.55), int(H * 0.80)),
          (int(W * 0.78), int(H * 0.76)),
          (W, int(H * 0.82))]
    stroke(img, fg, color=GOLD_DIM, width=1, alpha=160)


def m_barn(img):
    """Barn frame silhouette."""
    cx = W // 2
    base_y = int(H * 0.74)
    bw = 520
    bh = 280
    roof_h = 140
    half = bw // 2
    pts = [
        (cx - half, base_y),
        (cx - half, base_y - bh + roof_h),
        (cx, base_y - bh),
        (cx + half, base_y - bh + roof_h),
        (cx + half, base_y),
    ]
    stroke(img, pts + [pts[0]], color=GOLD, width=2, alpha=190)
    line(img, (cx, base_y - bh), (cx, base_y),
         color=GOLD_DIM, width=1, alpha=140)
    line(img, (cx - half, base_y - bh + roof_h),
         (cx + half, base_y - bh + roof_h),
         color=GOLD_DIM, width=1, alpha=140)
    line(img, (0, base_y), (W, base_y),
         color=GOLD_DIM, width=1, alpha=160)


def m_harvest(img):
    """Harvest grid — orchard rows from above."""
    cx = W // 2
    cy = H // 2
    rows, cols = 7, 14
    gap_x, gap_y = 78, 78
    for r in range(rows):
        for c in range(cols):
            x = cx + (c - cols / 2) * gap_x
            y = cy + (r - rows / 2) * gap_y
            r0 = 8
            ring(img, int(x), int(y), r0, color=GOLD,
                 width=1, alpha=130 + ((r + c) % 4) * 18)


def m_citrus(img):
    """Citrus / fruit cluster hint."""
    cx = int(W * 0.62)
    cy = int(H * 0.50)
    for k in range(11):
        ang = k / 11 * math.tau
        rr = 180 + (k % 3) * 40
        x = cx + int(math.cos(ang) * rr)
        y = cy + int(math.sin(ang) * rr * 0.85)
        ring(img, x, y, 36, color=GOLD, width=2, alpha=160)
        # Stem
        line(img, (x, y - 36), (x - 8, y - 60),
             color=GOLD_DIM, width=1, alpha=160)
    ring(img, cx, cy, 26, color=GOLD_HI, width=2, alpha=220)


def m_riverside(img):
    """Riverside topology — meandering line + faint shore lines."""
    pts = [(0, int(H * 0.55))]
    for i in range(1, 12):
        x = int(W * i / 11)
        y = int(H * (0.50 + 0.18 * math.sin(i * 0.9)))
        pts.append((x, y))
    pts.append((W, int(H * 0.55)))
    stroke(img, pts, color=GOLD, width=2, alpha=210)
    # Echo shores
    for k in range(1, 4):
        echo = [(p[0], p[1] + k * 14) for p in pts]
        stroke(img, echo, color=GOLD_DIM, width=1, alpha=130 - k * 24)


MOTIFS = [
    ("Cascades, on the record",       m_mountains,    "post-1.jpg"),
    ("Vineyard rows, Yakima Valley",  m_vineyard_rows, "post-2.jpg"),
    ("Quiet light, downtown",         m_window_grid,   "post-3.jpg"),
    ("On the riverside",              m_riverside,    "post-4.jpg"),
    ("Harvest grid",                  m_harvest,      "post-5.jpg"),
    ("Old barn",                      m_barn,         "post-6.jpg"),
    ("Arches",                        m_arches,       "post-7.jpg"),
    ("Staircase, west wall",          m_staircase,    "post-8.jpg"),
    ("Hatchwork",                     m_crosshatch,   "post-9.jpg"),
    ("Orchard cluster",               m_citrus,       "post-10.jpg"),
]


def render(idx: int, eyebrow: str, motif) -> Image.Image:
    img = base_canvas(W, H, seed=idx * 991)
    thin_grid(img, cols=14, rows=8, alpha=14)
    motif(img)
    diagonal_strokes(img, density=2)
    label_corner(img, eyebrow)
    watermark(img)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for idx, (eyebrow, motif, name) in enumerate(MOTIFS, start=1):
        img = render(idx, eyebrow, motif)
        save_jpeg(img, OUT / name)


if __name__ == "__main__":
    main()
