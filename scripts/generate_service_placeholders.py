"""Generate 12 unique 1200x900 (4:3) JPEGs for marketplace service placeholders.

Each motif maps to a marketplace category. Tasteful line art on warm-dark with
gold accents — never AI photo, never clipart.

Output: frontend/public/img/services/service-{1..12}.jpg
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import ImageDraw, Image

from _placeholder_common import (
    BLACK, GOLD, GOLD_DIM, GOLD_HI, MIST, PUBLIC_IMG, WARM,
    base_canvas, diagonal_strokes, filled_circle, font, label_corner, line,
    ring, save_jpeg, stroke, thin_grid, watermark,
)


W, H = 1200, 900
OUT = PUBLIC_IMG / "services"


def m_photography(img):
    """Lens grid — concentric rings + body box."""
    cx, cy = W // 2, H // 2 + 30
    for r in (40, 90, 140, 200, 260):
        ring(img, cx, cy, r, color=GOLD, width=2,
             alpha=200 if r < 140 else 130)
    # Aperture blades hint
    for k in range(8):
        a = k / 8 * math.tau
        x1 = cx + math.cos(a) * 60
        y1 = cy + math.sin(a) * 60
        x2 = cx + math.cos(a) * 130
        y2 = cy + math.sin(a) * 130
        line(img, (x1, y1), (x2, y2), color=GOLD_DIM, width=1, alpha=180)
    # Body box
    bw, bh = 540, 80
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((cx - bw // 2, cy - 320, cx + bw // 2, cy - 320 + bh),
                outline=(*GOLD, 200), width=2)


def m_drone(img):
    """Rotor arcs."""
    cx, cy = W // 2, H // 2
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x = cx + sx * 220
        y = cy + sy * 180
        ring(img, x, y, 70, color=GOLD, width=1, alpha=170)
        ring(img, x, y, 100, color=GOLD_DIM, width=1, alpha=120)
        line(img, (cx, cy), (x, y), color=GOLD, width=2, alpha=180)
    # Body
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((cx - 40, cy - 40, cx + 40, cy + 40),
                outline=(*GOLD_HI, 220), width=2)


def m_staging(img):
    """Sofa silhouette + lamp."""
    base_y = int(H * 0.72)
    sx, sw, sh = int(W * 0.22), int(W * 0.56), 200
    # Sofa
    pts = [
        (sx, base_y),
        (sx, base_y - sh + 40),
        (sx + 40, base_y - sh),
        (sx + sw - 40, base_y - sh),
        (sx + sw, base_y - sh + 40),
        (sx + sw, base_y),
    ]
    stroke(img, pts, color=GOLD, width=2, alpha=190)
    # Cushions
    for k in (0.25, 0.5, 0.75):
        x = sx + int(sw * k)
        line(img, (x, base_y - sh + 40), (x, base_y),
             color=GOLD_DIM, width=1, alpha=140)
    # Lamp
    lx = sx + sw + 110
    line(img, (lx, base_y), (lx, base_y - 320),
         color=GOLD_DIM, width=1, alpha=170)
    pts2 = [(lx - 60, base_y - 320), (lx + 60, base_y - 320),
            (lx + 30, base_y - 380), (lx - 30, base_y - 380), (lx - 60, base_y - 320)]
    stroke(img, pts2, color=GOLD, width=2, alpha=190)
    # Floor
    line(img, (0, base_y), (W, base_y),
         color=GOLD_DIM, width=1, alpha=160)


def m_lending(img):
    """Key fan — keyring with several keys."""
    cx, cy = int(W * 0.30), int(H * 0.50)
    ring(img, cx, cy, 50, color=GOLD, width=2, alpha=210)
    ring(img, cx, cy, 38, color=GOLD_DIM, width=1, alpha=160)
    angles = (-0.5, -0.2, 0.1, 0.4, 0.7)
    for a in angles:
        ex = cx + int(math.cos(a) * 380)
        ey = cy + int(math.sin(a) * 380)
        line(img, (cx + 50, cy), (ex, ey),
             color=GOLD, width=2, alpha=200)
        # Bit notches
        nx = ex - int(math.cos(a) * 60)
        ny = ey - int(math.sin(a) * 60)
        # Perpendicular notch
        px = -math.sin(a) * 14
        py = math.cos(a) * 14
        line(img, (nx, ny), (nx + px, ny + py),
             color=GOLD_HI, width=2, alpha=220)


def m_junk(img):
    """Truck silhouette."""
    base_y = int(H * 0.66)
    bx, bw, bh = int(W * 0.18), int(W * 0.42), 200
    d = ImageDraw.Draw(img, "RGBA")
    # Cargo box
    d.rectangle((bx, base_y - bh, bx + bw, base_y),
                outline=(*GOLD, 200), width=2)
    # Cab
    cx0 = bx + bw
    cw, ch = 200, 160
    pts = [
        (cx0, base_y),
        (cx0, base_y - ch),
        (cx0 + 50, base_y - ch - 30),
        (cx0 + cw - 30, base_y - ch - 30),
        (cx0 + cw, base_y - ch + 30),
        (cx0 + cw, base_y),
    ]
    stroke(img, pts, color=GOLD, width=2, alpha=200)
    # Wheels
    for x in (bx + 80, bx + bw - 80, cx0 + cw - 50):
        ring(img, x, base_y + 20, 36, color=GOLD_HI, width=2, alpha=220)
        ring(img, x, base_y + 20, 18, color=GOLD_DIM, width=1, alpha=160)
    # Ground
    line(img, (0, base_y + 56), (W, base_y + 56),
         color=GOLD_DIM, width=1, alpha=160)


def m_cleaning(img):
    """Bubble grid."""
    cx, cy = W // 2, H // 2
    for k in range(30):
        ang = (k * 137.5) * math.pi / 180
        rr = 30 + k * 14
        x = cx + int(math.cos(ang) * rr)
        y = cy + int(math.sin(ang) * rr * 0.9)
        size = 14 + (k % 5) * 6
        ring(img, x, y, size, color=GOLD, width=1,
             alpha=140 + (k % 4) * 20)
        if k % 4 == 0:
            ring(img, x - 4, y - 4, max(3, size // 4),
                 color=GOLD_HI, width=1, alpha=200)


def m_painting(img):
    """Roller + drip rail."""
    base_y = int(H * 0.50)
    rx, rw, rh = int(W * 0.20), int(W * 0.48), 50
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((rx, base_y, rx + rw, base_y + rh),
                outline=(*GOLD, 200), width=2)
    # Handle
    line(img, (rx + rw, base_y + rh // 2),
         (rx + rw + 220, base_y + rh // 2),
         color=GOLD_DIM, width=2, alpha=180)
    line(img, (rx + rw + 220, base_y + rh // 2 - 10),
         (rx + rw + 320, base_y + rh // 2 - 50),
         color=GOLD, width=2, alpha=190)
    # Drips
    for k in range(8):
        x = rx + int(rw * (0.1 + k * 0.11))
        line(img, (x, base_y + rh), (x, base_y + rh + 60 + (k % 4) * 30),
             color=GOLD, width=1, alpha=180)
    # Wall
    line(img, (0, base_y - 20), (W, base_y - 20),
         color=GOLD_DIM, width=1, alpha=120)


def m_landscape(img):
    """Tree row."""
    base_y = int(H * 0.74)
    cx_start = int(W * 0.10)
    gap = 130
    n = 8
    for i in range(n):
        x = cx_start + i * gap
        # Trunk
        line(img, (x, base_y), (x, base_y - 200),
             color=GOLD_DIM, width=2, alpha=200)
        # Crown
        ring(img, x, base_y - 230, 60, color=GOLD, width=2, alpha=190)
        ring(img, x - 14, base_y - 240, 36, color=GOLD_DIM, width=1, alpha=170)
        ring(img, x + 14, base_y - 220, 30, color=GOLD_DIM, width=1, alpha=170)
    line(img, (0, base_y), (W, base_y),
         color=GOLD, width=1, alpha=200)


def m_website(img):
    """Browser frame."""
    cx, cy = W // 2, H // 2
    bw, bh = 740, 460
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2),
                outline=(*GOLD, 210), width=2)
    # Tab bar
    line(img, (cx - bw // 2, cy - bh // 2 + 50),
         (cx + bw // 2, cy - bh // 2 + 50),
         color=GOLD, width=1, alpha=200)
    # Dots
    for i in range(3):
        cx0 = cx - bw // 2 + 28 + i * 28
        ring(img, cx0, cy - bh // 2 + 25, 8, color=GOLD_DIM,
             width=1, alpha=180)
    # Content lines
    for j in range(7):
        y = cy - bh // 2 + 100 + j * 40
        w_line = bw - 80
        if j % 3 == 2:
            w_line = int(w_line * 0.55)
        line(img, (cx - bw // 2 + 40, y),
             (cx - bw // 2 + 40 + w_line, y),
             color=GOLD_DIM, width=1, alpha=160)


def m_ai_node(img):
    """Node graph."""
    cx, cy = W // 2, H // 2
    nodes = []
    for k in range(7):
        ang = k / 7 * math.tau
        rr = 240
        x = cx + int(math.cos(ang) * rr)
        y = cy + int(math.sin(ang) * rr * 0.85)
        nodes.append((x, y))
    # Center node
    center = (cx, cy)
    # Connections
    for n in nodes:
        line(img, center, n, color=GOLD_DIM, width=1, alpha=140)
    for i, a in enumerate(nodes):
        b = nodes[(i + 2) % len(nodes)]
        line(img, a, b, color=GOLD_DIM, width=1, alpha=110)
    # Nodes
    for n in nodes:
        ring(img, n[0], n[1], 18, color=GOLD, width=2, alpha=220)
        filled_circle(img, n[0], n[1], 4, color=GOLD_HI, alpha=240)
    ring(img, center[0], center[1], 32, color=GOLD_HI, width=2, alpha=240)
    filled_circle(img, center[0], center[1], 10, color=GOLD, alpha=240)


def m_title_gavel(img):
    """Gavel + block — title / legal services."""
    base_y = int(H * 0.72)
    bx, bw, bh = int(W * 0.22), int(W * 0.36), 50
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((bx, base_y, bx + bw, base_y + bh),
                outline=(*GOLD, 200), width=2)
    # Gavel head
    hx, hy = int(W * 0.62), int(H * 0.36)
    d.rectangle((hx, hy, hx + 240, hy + 80),
                outline=(*GOLD, 220), width=2)
    line(img, (hx + 30, hy), (hx + 30, hy + 80),
         color=GOLD_DIM, width=1, alpha=180)
    line(img, (hx + 210, hy), (hx + 210, hy + 80),
         color=GOLD_DIM, width=1, alpha=180)
    # Handle
    line(img, (hx + 80, hy + 80),
         (hx + 80 - 200, hy + 80 + 360),
         color=GOLD, width=4, alpha=210)


def m_inspection(img):
    """Clipboard with checkmarks."""
    cx, cy = W // 2, H // 2
    bw, bh = 460, 600
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle((cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2),
                outline=(*GOLD, 220), width=2)
    # Clip
    d.rectangle((cx - 80, cy - bh // 2 - 40, cx + 80, cy - bh // 2 + 20),
                outline=(*GOLD_HI, 240), width=2)
    # Rows
    for j in range(7):
        y = cy - bh // 2 + 80 + j * 70
        # Checkbox
        d.rectangle((cx - bw // 2 + 50, y - 14,
                     cx - bw // 2 + 80, y + 14),
                    outline=(*GOLD, 200), width=2)
        # Check mark
        if j % 3 != 2:
            stroke(img, [(cx - bw // 2 + 56, y + 4),
                         (cx - bw // 2 + 64, y + 12),
                         (cx - bw // 2 + 78, y - 8)],
                   color=GOLD_HI, width=2, alpha=240)
        # Line
        w_line = bw - 180 if j % 4 != 3 else 240
        line(img, (cx - bw // 2 + 100, y),
             (cx - bw // 2 + 100 + w_line, y),
             color=GOLD_DIM, width=1, alpha=170)


MOTIFS = [
    ("Photography",     m_photography,  "service-1.jpg"),
    ("Drone tour",      m_drone,        "service-2.jpg"),
    ("Virtual staging", m_staging,      "service-3.jpg"),
    ("Lending",         m_lending,      "service-4.jpg"),
    ("Junk removal",    m_junk,         "service-5.jpg"),
    ("Cleaning",        m_cleaning,     "service-6.jpg"),
    ("Painting",        m_painting,     "service-7.jpg"),
    ("Landscape",       m_landscape,    "service-8.jpg"),
    ("Website",         m_website,      "service-9.jpg"),
    ("AI tools",        m_ai_node,      "service-10.jpg"),
    ("Title / legal",   m_title_gavel,  "service-11.jpg"),
    ("Inspection",      m_inspection,   "service-12.jpg"),
]


def render(idx: int, eyebrow: str, motif) -> Image.Image:
    img = base_canvas(W, H, seed=idx * 1117)
    thin_grid(img, cols=10, rows=8, alpha=14)
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
