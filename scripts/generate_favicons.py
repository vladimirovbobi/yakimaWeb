"""Generate favicon.ico + apple-touch-icon.png + icon-{192,512}.png.

Required deps: Pillow (already in pyproject.toml dev group). cairosvg optional —
not needed; we draw the mark directly via Pillow primitives so we never depend on
a system SVG renderer.

Output paths (all under frontend/public/):
    favicon.ico               (multi-size 16/32/48 ICO)
    apple-touch-icon.png      (180x180)
    icon-192.png              (192x192)
    icon-512.png              (512x512)

Runtime: ~1s on a laptop. Run via `make assets` or directly:

    python scripts/generate_favicons.py

The mark is the same compass-rose-style glyph used in logo-mark.svg —
gold (#BFA06A / #DEC98A) on a black (#080604) rounded square.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "public"

# Cream palette: cream-rounded surface, dark-ink mark, warm-gold ring accent.
# Pairs with manifest theme_color #F5EFE0 so the iOS/Android home-screen splash
# blends with the launched app shell.
CREAM = (245, 239, 224)
INK = (26, 18, 8)
GOLD = (139, 115, 64)
GOLD_HI = (184, 152, 96)


def _rounded_square(size: int, radius_ratio: float = 0.18) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = int(size * radius_ratio)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=r, fill=CREAM)
    return img


def _draw_mark(img: Image.Image) -> None:
    """Draw the compass-rose mark centered. Mark scales with image size."""
    size = img.size[0]
    cx = cy = size / 2.0
    # outer ring — warm-gold accent
    ring_r = size * 0.36
    ring_w = max(1, int(size * 0.035))
    d = ImageDraw.Draw(img)
    d.ellipse(
        (cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r),
        outline=GOLD,
        width=ring_w,
    )
    # 4-point star — dark ink for legibility on cream
    arm = size * 0.36
    blade = size * 0.045
    # vertical blade
    d.polygon(
        [
            (cx, cy - arm),
            (cx + blade, cy),
            (cx, cy + arm),
            (cx - blade, cy),
        ],
        fill=INK,
    )
    # horizontal blade
    d.polygon(
        [
            (cx - arm, cy),
            (cx, cy - blade),
            (cx + arm, cy),
            (cx, cy + blade),
        ],
        fill=INK,
    )
    # diagonal blades — gold accent, subtler
    diag = size * 0.255
    diag_b = size * 0.03
    for dx, dy in ((1, 1), (1, -1)):
        d.polygon(
            [
                (cx - diag * dx, cy - diag * dy),
                (cx + diag_b * dy, cy + diag_b * dx),
                (cx + diag * dx, cy + diag * dy),
                (cx - diag_b * dy, cy - diag_b * dx),
            ],
            fill=(*GOLD, 220),
        )
    # center dot — dark ink anchor
    dot = max(1, int(size * 0.025))
    d.ellipse((cx - dot, cy - dot, cx + dot, cy + dot), fill=INK)


def _make(size: int) -> Image.Image:
    img = _rounded_square(size)
    _draw_mark(img)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    # Multi-size ICO from a 256 source (Pillow downsamples internally)
    ico_src = _make(256)
    ico_path = OUT / "favicon.ico"
    ico_src.save(
        ico_path,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
    )

    apple = _make(180)
    apple.save(OUT / "apple-touch-icon.png", format="PNG", optimize=True)

    icon_192 = _make(192)
    icon_192.save(OUT / "icon-192.png", format="PNG", optimize=True)

    icon_512 = _make(512)
    icon_512.save(OUT / "icon-512.png", format="PNG", optimize=True)

    print(f"Wrote: {ico_path}")
    print(f"Wrote: {OUT / 'apple-touch-icon.png'}")
    print(f"Wrote: {OUT / 'icon-192.png'}")
    print(f"Wrote: {OUT / 'icon-512.png'}")


if __name__ == "__main__":
    main()
