"""Generic image upload endpoint for vendor onboarding + comment images.

POST /api/v1/uploads/?type=<upload_type>

Accepts a single multipart `file` field. Saves to `default_storage` under
`uploads/{user_id}/{ts}-{filename}.{ext}`, validates Pillow can decode it,
and returns the storage URL the FE stores in form state. Image moderation
is dispatched async (best-effort) on the `images` Celery queue.
"""

from __future__ import annotations

import logging
import os
import time
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils.text import get_valid_filename
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from apps.core.api.csrf import StrictCSRFMixin

log = logging.getLogger(__name__)
User = get_user_model()


class UploadThrottle(UserRateThrottle):
    """10 uploads/hour/user. Wired in REST_FRAMEWORK throttle rates."""

    scope = "upload"


UPLOAD_TYPES = {
    "service-hero": {"max_mb": 10, "allowed_mimes": ("image/jpeg", "image/png", "image/webp")},
    "service-gallery": {"max_mb": 10, "allowed_mimes": ("image/jpeg", "image/png", "image/webp")},
    "vendor-portfolio": {"max_mb": 10, "allowed_mimes": ("image/jpeg", "image/png", "image/webp")},
    "comment-image": {"max_mb": 5, "allowed_mimes": ("image/jpeg", "image/png", "image/webp")},
    "user-avatar": {"max_mb": 5, "allowed_mimes": ("image/jpeg", "image/png", "image/webp")},
    "realtor-headshot": {"max_mb": 5, "allowed_mimes": ("image/jpeg", "image/png", "image/webp")},
    "flyer-photo": {"max_mb": 10, "allowed_mimes": ("image/jpeg", "image/png", "image/webp")},
}

# Map filename suffix to canonical mime — we don't trust client-supplied content_type alone.
_MIME_BY_EXT: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


def _probe_image(blob: bytes) -> str:
    """Return the Pillow-detected MIME type. Raises ValidationError on bad bytes.

    Catches Pillow's DecompressionBombError explicitly (SEC-018) so a malicious
    high-compression image that decodes to billions of pixels surfaces as a
    clean 400 instead of a 500 from an OOM.
    """
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError as exc:  # pragma: no cover — Pillow is in the env
        raise ValidationError({"file": "Image processing unavailable."}) from exc

    try:
        img = Image.open(BytesIO(blob))
        img.verify()
    except Image.DecompressionBombError as exc:
        raise ValidationError(
            {"file": "Image too large to process safely."},
        ) from exc
    except (UnidentifiedImageError, Exception) as exc:
        raise ValidationError({"file": "File is not a valid image."}) from exc

    fmt = (img.format or "").lower()
    return {
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
    }.get(fmt, "")


class ImageUploadView(StrictCSRFMixin, generics.GenericAPIView):
    """POST /api/v1/uploads/?type=<upload_type>.

    Returns:
        {url, alt: "", uploaded_at: ISO8601, type}
    """

    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)
    throttle_classes = (UploadThrottle,)

    def post(self, request, *args, **kwargs):
        upload_type = (request.query_params.get("type") or "").strip()
        if upload_type not in UPLOAD_TYPES:
            raise ValidationError(
                {"type": f"Must be one of {sorted(UPLOAD_TYPES)}."},
            )

        rules = UPLOAD_TYPES[upload_type]
        upload = request.FILES.get("file")
        if upload is None:
            raise ValidationError({"file": "No file uploaded."})

        max_bytes = rules["max_mb"] * 1024 * 1024
        size = getattr(upload, "size", 0) or 0
        if size > max_bytes:
            raise ValidationError(
                {"file": f"File exceeds max size ({rules['max_mb']} MB)."},
            )
        if size == 0:
            raise ValidationError({"file": "File is empty."})

        # Validate extension/mime — accept only allowed_mimes.
        original = upload.name or "upload.bin"
        ext = os.path.splitext(original)[1].lower()
        ext_mime = _MIME_BY_EXT.get(ext, "")
        client_mime = (getattr(upload, "content_type", "") or "").lower().split(";")[0].strip()
        if ext_mime and ext_mime not in rules["allowed_mimes"]:
            raise ValidationError(
                {"file": f"Disallowed extension {ext}."},
            )
        if client_mime and client_mime not in rules["allowed_mimes"]:
            raise ValidationError(
                {"file": f"Disallowed content type {client_mime}."},
            )

        # Pillow probe — must succeed AND the detected mime must match the allowlist.
        blob = upload.read()
        detected = _probe_image(blob)
        if detected and detected not in rules["allowed_mimes"]:
            raise ValidationError(
                {"file": f"Image format {detected} is not allowed."},
            )

        # Build storage path.
        safe_name = get_valid_filename(original)[:120] or "upload.bin"
        ts = int(time.time())
        storage_path = f"uploads/{request.user.pk}/{ts}-{safe_name}"
        saved_path = default_storage.save(storage_path, ContentFile(blob))
        url = default_storage.url(saved_path)

        # Best-effort: run image through moderation pipeline async on the images queue.
        try:
            from django.contrib.contenttypes.models import ContentType

            from apps.moderation.tasks import moderate_image_task

            user_ct = ContentType.objects.get_for_model(User)
            moderate_image_task.apply_async(
                args=[user_ct.pk, request.user.pk],
                kwargs={"image_attr": "avatar"},
                queue="images",
            )
        except Exception:  # noqa: BLE001
            log.debug("upload moderation dispatch failed", exc_info=True)

        from django.utils import timezone

        return Response(
            {
                "url": url,
                "path": saved_path,
                "alt": "",
                "uploaded_at": timezone.now().isoformat(),
                "type": upload_type,
            },
            status=status.HTTP_201_CREATED,
        )
