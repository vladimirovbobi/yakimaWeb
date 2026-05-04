"""Generate placeholder before/after pairs for the furniture-remover demo.

Pure Pillow — no external photo assets, no AI generation. Three pairs of 1200x900
JPEGs that read as deliberate placeholders ("DEMO" watermark + "demo placeholder"
subtitle) so they cannot accidentally ship as final art.

Required deps: Pillow.

Output: frontend/public/img/samples/furniture-remover/
    before-1.jpg, before-2.jpg, before-3.jpg
    after-1.jpg,  after-2.jpg,  after-3.jpg

Runtime: ~2s. Run via `make assets` or directly:

    python scripts/generate_furniture_remover_samples.py

Replace with real photographer-supplied pairs before launch.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "frontend" / "public" / "img" / "samples" / "furniture-remover"

W, H = 1200, 900

# Brand tokens
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
    """Try to load DejaVu (always shipped with Pillow). Fall back to default."""
    candidates = (
        ["DejaVuSerif-Bold.ttf"] if bold else ["DejaVuSerif.ttf"]
    ) + ["DejaVuSans.ttf"]
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _gradient(top: tuple, bottom: tuple) -> Image.Image:
    img = Image.new("RGB", (W, H), top)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / max(1, H - 1)
        r = int(top[0] + (bottom[0] - top[0]) * t)
        g = int(top[1] + (bottom[1] - top[1]) * t)
        b = int(top[2] + (bottom[2] - top[2]) * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))
    return img


def _draw_room(img: Image.Image, *, furnished: bool) -> None:
    """Sketch a simple room scene with line-art so it reads as a room.

    Floor + back wall + window + (optional) sofa + (optional) coffee table.
    """
    d = ImageDraw.Draw(img)
    # Floor line (perspective)
    floor_y = int(H * 0.66)
    d.line([(0, floor_y), (W, floor_y)], fill=GOLD_DIM, width=2)
    # Back wall trim
    trim_y = int(H * 0.18)
    d.line([(0, trim_y), (W, trim_y)], fill=GOLD_DIM, width=1)
    # Window
    win_x1, win_y1 = int(W * 0.62), int(H * 0.24)
    win_x2, win_y2 = int(W * 0.86), int(H * 0.58)
    d.rectangle((win_x1, win_y1, win_x2, win_y2), outline=GOLD, width=2)
    d.line([((win_x1 + win_x2) // 2, win_y1),
            ((win_x1 + win_x2) // 2, win_y2)], fill=GOLD_DIM, width=1)
    d.line([(win_x1, (win_y1 + win_y2) // 2),
            (win_x2, (win_y1 + win_y2) // 2)], fill=GOLD_DIM, width=1)

    if furnished:
        # Sofa
        sx1, sy1 = int(W * 0.10), int(H * 0.55)
        sx2, sy2 = int(W * 0.50), int(H * 0.78)
        d.rectangle((sx1, sy1, sx2, sy2), outline=GOLD, width=2)
        # Sofa cushions
        cw = (sx2 - sx1) // 3
        for i in range(1, 3):
            x = sx1 + cw * i
            d.line([(x, sy1 + 8), (x, sy2 - 8)], fill=GOLD_DIM, width=1)
        # Sofa back line
        d.line([(sx1, sy1 + 24), (sx2, sy1 + 24)], fill=GOLD_DIM, width=1)
        # Coffee table
        tx1, ty1 = int(W * 0.18), int(H * 0.82)
        tx2, ty2 = int(W * 0.42), int(H * 0.88)
        d.rectangle((tx1, ty1, tx2, ty2), outline=GOLD, width=2)


def _watermark(img: Image.Image, label: str) -> None:
    """Diagonal repeating "DEMO" watermark + corner pip."""
    d = ImageDraw.Draw(img, "RGBA")
    f_big = _font(120, bold=True)
    f_pip = _font(20, bold=True)

    # Diagonal stamp (single, large, semi-transparent)
    text = "DEMO"
    bbox = d.textbbox((0, 0), text, font=f_big)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    stamp = Image.new("RGBA", (tw + 40, th + 40), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stamp)
    sd.text((20, 20), text, font=f_big, fill=(*GOLD, 70))
    rotated = stamp.rotate(-22, resample=Image.BICUBIC, expand=True)
    img.paste(
        rotated,
        ((W - rotated.width) // 2, (H - rotated.height) // 2),
        rotated,
    )

    # Corner pip
    pip_text = "[demo]"
    bbox = d.textbbox((0, 0), pip_text, font=f_pip)
    pip_w = bbox[2] - bbox[0]
    pip_h = bbox[3] - bbox[1]
    margin = 24
    pad = 8
    rect = (
        W - margin - pip_w - pad * 2,
        H - margin - pip_h - pad * 2,
        W - margin,
        H - margin,
    )
    d.rectangle(rect, fill=(*BLACK, 220), outline=GOLD)
    d.text(
        (rect[0] + pad, rect[1] + pad - 2),
        pip_text,
        font=f_pip,
        fill=GOLD_HI,
    )

    # Label is set elsewhere; this is just the watermark
    _ = label


def _render_card(*, furnished: bool, idx: int) -> Image.Image:
    if furnished:
        img = _gradient(WARM, DEEP)
    else:
        img = _gradient(PANEL, BLACK)

    _draw_room(img, furnished=furnished)

    d = ImageDraw.Draw(img)
    # Eyebrow
    eyebrow_font = _font(22, bold=True)
    eyebrow = "FURNITURE REMOVER  ·  SAMPLE"
    d.text((48, 36), eyebrow, font=eyebrow_font, fill=GOLD)
    # Tiny gold rule under eyebrow
    d.line([(48, 70), (140, 70)], fill=GOLD, width=2)

    # Title
    title_font = _font(72, bold=True)
    title = "Furnished Living Room — Before" if furnished else "Empty Room — After"
    d.text((48, 96), title, font=title_font, fill=GOLD_HI)

    # Subtitle
    sub_font = _font(28)
    d.text((48, 188), "demo placeholder", font=sub_font, fill=MIST)

    # Pair number bottom-left
    pair_font = _font(20, bold=True)
    d.text((48, H - 60), f"PAIR  ·  0{idx}/03", font=pair_font, fill=GOLD)

    _watermark(img, "before" if furnished else "after")
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for i in (1, 2, 3):
        before = _render_card(furnished=True, idx=i)
        before.save(OUT / f"before-{i}.jpg", format="JPEG", quality=82, optimize=True)
        after = _render_card(furnished=False, idx=i)
        after.save(OUT / f"after-{i}.jpg", format="JPEG", quality=82, optimize=True)
        print(f"Wrote: {OUT / f'before-{i}.jpg'}")
        print(f"Wrote: {OUT / f'after-{i}.jpg'}")


if __name__ == "__main__":
    main()
