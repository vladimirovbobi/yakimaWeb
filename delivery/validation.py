"""Per-file validation rules — extension, size, content sniff.

Server-validated on every upload. Client validation in the UI is UX only.
"""
from __future__ import annotations

from dataclasses import dataclass

from config import get_settings


IMAGE_EXTS    = {"jpg", "jpeg", "png", "webp", "heic", "heif", "tiff", "tif"}
ARCHIVE_EXTS  = {"zip", "7z"}
DOCUMENT_EXTS = {"pdf", "docx"}
WORKFLOW_EXTS = {"json"}

ALLOWED_EXTS = IMAGE_EXTS | ARCHIVE_EXTS | DOCUMENT_EXTS | WORKFLOW_EXTS

# Magic-byte prefixes for the formats we accept. We don't trust the
# `Content-Type` header from the upload — the file gets sniffed.
MAGIC_BYTES: list[tuple[str, bytes]] = [
    ("jpg",  b"\xff\xd8\xff"),
    ("png",  b"\x89PNG\r\n\x1a\n"),
    ("webp", b"RIFF"),                      # webp is RIFF + WEBP, see header_check
    ("heic", b"\x00\x00\x00"),               # heic is ftypheic at offset 4 — see header_check
    ("tif",  b"II*\x00"),
    ("tif",  b"MM\x00*"),
    ("zip",  b"PK\x03\x04"),
    ("7z",   b"7z\xbc\xaf\x27\x1c"),
    ("pdf",  b"%PDF-"),
    ("docx", b"PK\x03\x04"),                 # docx is a zip
    ("json", b"{"),
    ("json", b"["),
]


@dataclass
class FileValidationResult:
    allowed: bool
    category: str
    reason: str = ""


def _ext_from_filename(name: str) -> str:
    return (name.rsplit(".", 1)[-1] if "." in name else "").lower()


def _category_for_ext(ext: str) -> str:
    if ext in IMAGE_EXTS: return "image"
    if ext in ARCHIVE_EXTS: return "archive"
    if ext in DOCUMENT_EXTS: return "document"
    if ext in WORKFLOW_EXTS: return "workflow"
    return "unknown"


def _max_size_for_category(cat: str) -> int:
    s = get_settings()
    return {
        "image":    s.max_file_size_image,
        "archive":  s.max_file_size_archive,
        "document": s.max_file_size_document,
        "workflow": s.max_file_size_workflow,
    }.get(cat, 0)


def _header_matches(payload: bytes, ext: str) -> bool:
    """Magic-byte sniff. Some formats need a deeper look."""
    head = payload[:32]
    if ext == "webp":
        # RIFF????WEBP
        return head.startswith(b"RIFF") and head[8:12] == b"WEBP"
    if ext in ("heic", "heif"):
        return b"ftypheic" in head or b"ftypmif1" in head or b"ftypmsf1" in head
    if ext == "json":
        # JSON can start with whitespace; strip.
        stripped = payload.lstrip()[:1]
        return stripped in (b"{", b"[")
    for ext_marker, magic in MAGIC_BYTES:
        if ext == ext_marker and head.startswith(magic):
            return True
    return False


def validate_upload(filename: str, payload: bytes) -> FileValidationResult:
    ext = _ext_from_filename(filename)
    if ext not in ALLOWED_EXTS:
        return FileValidationResult(False, "unknown", f"extension '.{ext}' not allowed")
    category = _category_for_ext(ext)
    max_size = _max_size_for_category(category)
    if max_size and len(payload) > max_size:
        return FileValidationResult(
            False, category, f"size {len(payload)} > limit {max_size} for {category}"
        )
    if not _header_matches(payload, ext):
        return FileValidationResult(False, category, "magic bytes do not match extension")
    return FileValidationResult(True, category, "")
