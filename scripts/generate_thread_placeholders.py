"""Generate 6 unique 1200x675 (16:9) JPEGs for forum thread placeholders.

Conversation-feel motifs — speech bubbles, dashed topology, comment lattice.

Output: frontend/public/img/threads/thread-{1..6}.jpg
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import ImageDraw, Image

from _placeholder_common import (
    BLACK, GOLD, GOLD_DIM, GOLD_HI, MIST, PUBLIC_IMG, WARM,
    base_canvas, diagonal_strokes, filled_circle, label_corner, line,
    ring, save_jpeg, stroke, thin_grid, watermark,
)


W, H = 1200, 675
OUT = PUBLIC_IMG / "threads"


def _bubble(img, cx, cy, w, h, color=GOLD, alpha=200, tail="left"):
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2),
                        radius=18, outline=(*color, alpha), width=2)
    # tail
    if tail == "left":
        pts = [(cx - w // 2 + 10, cy + h // 2),
               (cx - w // 2 - 18, cy + h // 2 + 26),
               (cx - w // 2 + 40, cy + h // 2)]
    else:
        pts = [(cx + w // 2 - 10, cy + h // 2),
               (cx + w // 2 + 18, cy + h // 2 + 26),
               (cx + w // 2 - 40, cy + h // 2)]
    stroke(img, pts, color=color, width=2, alpha=alpha)
    # Three lines inside the bubble to suggest text
    for j in range(3):
        line(img,
             (cx - w // 2 + 22, cy - h // 2 + 22 + j * 18),
             (cx + w // 2 - 22 - (j * 28), cy - h // 2 + 22 + j * 18),
             color=GOLD_DIM, width=1, alpha=160)


def m_speech_grid(img):
    bubbles = [
        (300, 220, 320, 110, GOLD,    "left"),
        (820, 200, 280, 100, GOLD_HI, "right"),
        (380, 410, 420, 130, GOLD,    "left"),
        (900, 460, 240, 90,  GOLD_DIM, "right"),
    ]
    for cx, cy, w, h, color, tail in bubbles:
        _bubble(img, cx, cy, w, h, color=color, alpha=210, tail=tail)


def m_dashed_topology(img):
    """Dashed line + nodes — discussion-thread feel."""
    pts = [(80, 160), (320, 220), (520, 180), (740, 280),
           (940, 220), (1120, 320)]
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        steps = 18
        for k in range(steps):
            if k % 2:
                continue
            t1 = k / steps
            t2 = (k + 1) / steps
            line(img,
                 (x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1),
                 (x1 + (x2 - x1) * t2, y1 + (y2 - y1) * t2),
                 color=GOLD, width=2, alpha=210)
    for x, y in pts:
        ring(img, x, y, 14, color=GOLD_HI, width=2, alpha=240)
        filled_circle(img, x, y, 5, color=GOLD, alpha=240)
    # Reply branch
    branch = [(740, 280), (660, 420), (820, 480), (960, 460)]
    for i in range(len(branch) - 1):
        line(img, branch[i], branch[i + 1],
             color=GOLD_DIM, width=1, alpha=180)
    for x, y in branch[1:]:
        ring(img, x, y, 10, color=GOLD_DIM, width=1, alpha=200)


def m_comment_lattice(img):
    """Stacked comment cards."""
    cards = [
        (140, 140, 920, 100, GOLD),
        (180, 280, 780, 100, GOLD_DIM),
        (220, 420, 680, 100, GOLD_DIM),
        (260, 560, 580, 80,  GOLD_DIM),
    ]
    d = ImageDraw.Draw(img, "RGBA")
    for x, y, w, h, color in cards:
        d.rounded_rectangle((x, y, x + w, y + h),
                            radius=10, outline=(*color, 220), width=2)
        # Avatar
        ring(img, x + 30, y + h // 2, 18, color=GOLD, width=2, alpha=220)
        # text lines
        line(img, (x + 70, y + 28),
             (x + 70 + (w - 110), y + 28),
             color=GOLD_DIM, width=1, alpha=160)
        line(img, (x + 70, y + 52),
             (x + 70 + int((w - 110) * 0.7), y + 52),
             color=GOLD_DIM, width=1, alpha=140)


def m_quote_marks(img):
    cx, cy = W // 2, H // 2
    d = ImageDraw.Draw(img, "RGBA")
    # Big stylized open-quote
    for sx in (-1, 1):
        x = cx + sx * 240
        d.rounded_rectangle((x - 70, cy - 80, x + 50, cy - 10),
                            radius=8, outline=(*GOLD, 220), width=3)
        line(img, (x - 30, cy - 10), (x - 50, cy + 50),
             color=GOLD, width=3, alpha=220)
        line(img, (x + 20, cy - 10), (x, cy + 50),
             color=GOLD, width=3, alpha=220)
    # Center line
    line(img, (cx - 280, cy + 100), (cx + 280, cy + 100),
         color=GOLD_HI, width=2, alpha=220)


def m_radial_replies(img):
    """Center node with replies fanned out."""
    cx, cy = W // 2, H // 2
    ring(img, cx, cy, 50, color=GOLD, width=3, alpha=240)
    filled_circle(img, cx, cy, 12, color=GOLD_HI, alpha=240)
    for k in range(9):
        a = k / 9 * math.tau
        ex = cx + int(math.cos(a) * 240)
        ey = cy + int(math.sin(a) * 240 * 0.78)
        line(img, (cx + int(math.cos(a) * 50), cy + int(math.sin(a) * 50)),
             (ex, ey), color=GOLD_DIM, width=1, alpha=180)
        ring(img, ex, ey, 18, color=GOLD, width=2, alpha=210)


def m_threadline(img):
    """Vertical timeline of replies."""
    x_axis = W // 2 - 220
    line(img, (x_axis, 80), (x_axis, H - 80),
         color=GOLD, width=2, alpha=210)
    for i in range(5):
        y = 130 + i * 100
        ring(img, x_axis, y, 12, color=GOLD_HI, width=2, alpha=240)
        line(img, (x_axis + 12, y), (x_axis + 80, y),
             color=GOLD_DIM, width=1, alpha=200)
        line(img, (x_axis + 80, y), (x_axis + 80 + 380 - i * 40, y),
             color=GOLD, width=2, alpha=210)
        line(img, (x_axis + 80, y + 14),
             (x_axis + 80 + int(360 * (1 - i * 0.12)), y + 14),
             color=GOLD_DIM, width=1, alpha=170)


MOTIFS = [
    ("Buying",        m_speech_grid,     "thread-1.jpg"),
    ("Selling",       m_dashed_topology, "thread-2.jpg"),
    ("Market",        m_comment_lattice, "thread-3.jpg"),
    ("Ask Yakima",    m_quote_marks,     "thread-4.jpg"),
    ("Vendors",       m_radial_replies,  "thread-5.jpg"),
    ("Neighborhoods", m_threadline,      "thread-6.jpg"),
]


def render(idx: int, eyebrow: str, motif) -> Image.Image:
    img = base_canvas(W, H, seed=idx * 587 + 13)
    thin_grid(img, cols=12, rows=7, alpha=12)
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
