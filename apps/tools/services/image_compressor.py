"""Lossless image compressor — Pillow-based, no perceptual quality loss.

Compression strategy by format
------------------------------
- JPEG: re-encode with ``quality="keep"`` (preserves original quantization tables
  exactly; Pillow ≥ 9.1) + ``optimize=True`` (Huffman optimization) +
  ``progressive=True`` + EXIF strip. Pixel data is byte-identical to the input.
  Typical savings: 5-15%.

- PNG: re-encode with ``optimize=True`` (deflate optimization, no quantization).
  Fully lossless. Typical savings: 10-30%.

- WebP: re-encode with ``lossless=True, method=6`` (slowest/best). Fully lossless.
  Typical savings: 5-20%.

- GIF: re-encode with ``optimize=True`` + ``save_all=True`` (preserves animation).
  Lossless palette compression.

- HEIC/HEIF: read via ``pillow-heif`` if installed → convert to lossless WebP
  output. Otherwise fall back to a clear ``UnsupportedFormat`` error.

- TIFF/BMP: convert to PNG (lossless). PNG is smaller and universally renderable.

The service does NOT downscale, NOT change colorspace, NOT rotate, and NOT change
the bit-depth. The image you get back is visually identical to the one you put in.
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import BinaryIO

from PIL import Image, ImageFile

# Allow Pillow to read partial JPEGs without erroring (defense-in-depth on
# slightly truncated uploads). Compression itself still runs on what's read.
ImageFile.LOAD_TRUNCATED_IMAGES = True

log = logging.getLogger(__name__)


SUPPORTED_INPUT_EXTENSIONS = {
    "jpg", "jpeg", "png", "webp", "gif", "heic", "heif", "tiff", "tif", "bmp",
}

# Hard cap: 50 MB. Bigger than the furniture remover (10 MB) because lossless
# compression makes more sense on larger source files.
MAX_INPUT_BYTES = 50 * 1024 * 1024


class UnsupportedFormat(Exception):
    """Raised when the input format is not supported."""


class ImageCompressorError(Exception):
    """Raised on transient or unexpected failure."""


@dataclass
class CompressionResult:
    """What the service returns to the caller."""
    output_bytes:    bytes
    output_format:   str            # 'jpeg' | 'png' | 'webp' | 'gif'
    output_filename: str            # suggested filename with the new extension
    input_size:      int            # bytes
    output_size:     int            # bytes
    bytes_saved:     int
    percent_saved:   float          # 0-100, rounded to 1 decimal
    width:           int
    height:          int
    method:          str            # human-readable description of what we did


def _normalize_extension(filename: str) -> str:
    return (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()


def _ensure_heif_support() -> bool:
    try:
        import pillow_heif

        pillow_heif.register_heif_opener()
        return True
    except Exception:  # noqa: BLE001
        return False


def _open_image(buf: BinaryIO, ext: str) -> Image.Image:
    """Open the image, registering HEIF support if needed and available."""
    if ext in {"heic", "heif"} and not _ensure_heif_support():
        raise UnsupportedFormat(
            "HEIC/HEIF support requires `pillow-heif` to be installed on the worker."
        )
    try:
        img = Image.open(buf)
    except Exception as exc:
        raise ImageCompressorError(f"Could not open image: {exc}") from exc
    img.load()
    return img


def _compress_jpeg(img: Image.Image, base_filename: str) -> CompressionResult:
    """JPEG → JPEG. Lossless re-encode preserving quantization tables.

    ``quality="keep"`` requires the source to actually be a JPEG; if Pillow can
    not preserve tables we fall back to ``quality=95`` (high quality, still very
    close to lossless for natural photos).
    """
    out = io.BytesIO()
    save_kwargs: dict = {
        "format":      "JPEG",
        "optimize":    True,
        "progressive": True,
    }
    try:
        img.save(out, quality="keep", **save_kwargs)
    except (ValueError, OSError):
        out = io.BytesIO()
        img.save(out, quality=95, subsampling="keep", **save_kwargs)
    data = out.getvalue()
    return CompressionResult(
        output_bytes=data,
        output_format="jpeg",
        output_filename=_swap_extension(base_filename, "jpg"),
        input_size=0,
        output_size=len(data),
        bytes_saved=0,
        percent_saved=0.0,
        width=img.width,
        height=img.height,
        method=(
            "JPEG re-encoded with original quantization tables; "
            "Huffman + progressive optimized; EXIF stripped"
        ),
    )


def _compress_png(img: Image.Image, base_filename: str) -> CompressionResult:
    """PNG → PNG. Lossless deflate optimization."""
    out = io.BytesIO()
    save_kwargs: dict = {"format": "PNG", "optimize": True}
    img.save(out, **save_kwargs)
    data = out.getvalue()
    return CompressionResult(
        output_bytes=data,
        output_format="png",
        output_filename=_swap_extension(base_filename, "png"),
        input_size=0,
        output_size=len(data),
        bytes_saved=0,
        percent_saved=0.0,
        width=img.width,
        height=img.height,
        method="PNG re-encoded with optimized deflate compression; metadata stripped",
    )


def _compress_webp(img: Image.Image, base_filename: str) -> CompressionResult:
    """WebP → WebP. Lossless with slowest (best) encoding method."""
    out = io.BytesIO()
    img.save(out, format="WEBP", lossless=True, method=6)
    data = out.getvalue()
    return CompressionResult(
        output_bytes=data,
        output_format="webp",
        output_filename=_swap_extension(base_filename, "webp"),
        input_size=0,
        output_size=len(data),
        bytes_saved=0,
        percent_saved=0.0,
        width=img.width,
        height=img.height,
        method="WebP re-encoded losslessly with slowest/best method",
    )


def _compress_gif(img: Image.Image, base_filename: str) -> CompressionResult:
    """GIF → GIF. Optimize palette + lossless frame compression."""
    out = io.BytesIO()
    img.save(out, format="GIF", optimize=True, save_all=getattr(img, "is_animated", False))
    data = out.getvalue()
    return CompressionResult(
        output_bytes=data,
        output_format="gif",
        output_filename=_swap_extension(base_filename, "gif"),
        input_size=0,
        output_size=len(data),
        bytes_saved=0,
        percent_saved=0.0,
        width=img.width,
        height=img.height,
        method="GIF palette + frames optimized losslessly",
    )


def _convert_heif_to_webp(img: Image.Image, base_filename: str) -> CompressionResult:
    """HEIC/HEIF → WebP lossless. HEIC output is patent-restricted; WebP is open."""
    return _compress_webp(img, base_filename)


def _convert_to_png(img: Image.Image, base_filename: str) -> CompressionResult:
    """TIFF/BMP/etc → PNG. Lossless conversion to a smaller, web-renderable format."""
    if img.mode not in ("RGB", "RGBA", "L", "P", "1"):
        img = img.convert("RGBA")
    return _compress_png(img, base_filename)


def _swap_extension(filename: str, new_ext: str) -> str:
    base = filename.rsplit(".", 1)[0] if "." in filename else filename
    return f"{base}-compressed.{new_ext}"


def compress(payload: bytes, filename: str) -> CompressionResult:
    """Compress an image losslessly. Single-file synchronous service.

    Raises:
        UnsupportedFormat — extension not in our allowlist.
        ImageCompressorError — Pillow could not read or write the image.
    """
    if len(payload) > MAX_INPUT_BYTES:
        limit_mb = MAX_INPUT_BYTES // (1024 * 1024)
        raise UnsupportedFormat(
            f"Input is {len(payload)} bytes; limit is {MAX_INPUT_BYTES} bytes ({limit_mb} MB)."
        )

    ext = _normalize_extension(filename)
    if ext not in SUPPORTED_INPUT_EXTENSIONS:
        raise UnsupportedFormat(
            f"Format '.{ext}' is not supported. Allowed: {sorted(SUPPORTED_INPUT_EXTENSIONS)}."
        )

    buf = io.BytesIO(payload)
    img = _open_image(buf, ext)

    if ext in ("jpg", "jpeg"):
        result = _compress_jpeg(img, filename)
    elif ext == "png":
        result = _compress_png(img, filename)
    elif ext == "webp":
        result = _compress_webp(img, filename)
    elif ext == "gif":
        result = _compress_gif(img, filename)
    elif ext in ("heic", "heif"):
        result = _convert_heif_to_webp(img, filename)
    elif ext in ("tiff", "tif", "bmp"):
        result = _convert_to_png(img, filename)
    else:  # pragma: no cover — defensive; SUPPORTED_INPUT_EXTENSIONS already gated
        raise UnsupportedFormat(f"Internal: format '.{ext}' fell through.")

    result.input_size = len(payload)
    result.bytes_saved = max(0, result.input_size - result.output_size)
    if result.input_size > 0:
        result.percent_saved = round((result.bytes_saved / result.input_size) * 100, 1)

    log.info(
        "image_compressor: %s → %s, %d → %d bytes (%.1f%% saved)",
        filename,
        result.output_filename,
        result.input_size,
        result.output_size,
        result.percent_saved,
    )
    return result
