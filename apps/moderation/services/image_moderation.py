"""Image moderation — deterministic checks + Gemini Pro vision pass.

Same fail-closed contract as text moderation: parse errors default to QUEUE,
never APPROVE. Wired into Comment.image post_save signal.

Layer 1 (deterministic): size/mime/dimension cap.
Layer 2 (vision LLM): Gemini Pro multimodal — 'is this image safe? returns JSON'.
Layer 3 (human queue): everything that didn't approve cleanly.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass

from django.conf import settings

log = logging.getLogger(__name__)

MAX_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_PREFIX = ("image/jpeg", "image/png", "image/webp", "image/gif")

CLASSIFIER_VERSION = "image_moderation_v1"

DEFAULT_FAIL = {
    "allowed": False,
    "categories": ["malformed_response"],
    "severity": 3,
    "reason": "image classifier returned invalid response",
    "action": "queue",
}

VISION_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "allowed": {"type": "boolean"},
        "categories": {
            "type": "array",
            "items": {"type": "string", "enum": [
                "ok", "nudity", "violence", "hateful_imagery",
                "personal_info", "weapons", "policy_violation", "low_quality",
            ]},
        },
        "severity": {"type": "integer", "minimum": 1, "maximum": 4},
        "reason": {"type": "string", "maxLength": 300},
        "action": {"type": "string", "enum": ["approve", "queue", "remove"]},
    },
    "required": ["allowed", "categories", "severity", "reason", "action"],
}

VISION_PROMPT = (
    "You are an image moderator for Yakima Real Estate Hub.\n"
    "Decide if the user-uploaded image is safe to show on a public real-estate platform.\n"
    "REMOVE: nudity, sexual content, violence, hateful symbols, weapons, doxxing (visible "
    "license plates, IDs, credit cards), spam/advertising overlays.\n"
    "QUEUE: low quality, blurry, off-topic, ambiguous.\n"
    "APPROVE: real-estate-relevant photos (homes, neighborhoods, profile pics).\n"
    "Return JSON only — never include the rationale in plain text outside the schema.\n"
)


@dataclass
class ModerationResult:
    allowed: bool
    categories: list[str]
    severity: int
    reason: str
    action: str


def _parse_vision_response(raw: str) -> dict:
    """Strict parse — fail closed on any deviation."""
    if not raw or not isinstance(raw, str):
        return dict(DEFAULT_FAIL)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned).strip()
    try:
        parsed = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return dict(DEFAULT_FAIL)
    if not isinstance(parsed, dict):
        return dict(DEFAULT_FAIL)
    required = {"allowed", "categories", "severity", "reason", "action"}
    if not required.issubset(parsed.keys()):
        return dict(DEFAULT_FAIL)
    if parsed.get("action") not in {"approve", "queue", "remove"}:
        return dict(DEFAULT_FAIL)
    if parsed.get("severity") not in {1, 2, 3, 4}:
        return dict(DEFAULT_FAIL)
    if not isinstance(parsed.get("allowed"), bool):
        return dict(DEFAULT_FAIL)
    if not isinstance(parsed.get("categories"), list):
        return dict(DEFAULT_FAIL)
    return parsed


def hash_image(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


def deterministic_image_check(
    image_bytes: bytes, *, mime: str = "",
) -> ModerationResult | None:
    """Hard rejects before any LLM call. Returns None if clean."""
    if not image_bytes:
        return ModerationResult(
            allowed=False, categories=["empty"], severity=4,
            reason="empty image", action="remove",
        )
    if len(image_bytes) > MAX_BYTES:
        return ModerationResult(
            allowed=False, categories=["oversized"], severity=3,
            reason="image exceeds 10 MB", action="remove",
        )
    if mime and not mime.startswith(ALLOWED_MIME_PREFIX):
        return ModerationResult(
            allowed=False, categories=["bad_mime"], severity=3,
            reason=f"unsupported mime: {mime}", action="remove",
        )
    return None


def _call_gemini_vision(image_bytes: bytes, mime: str) -> str:
    """Real Gemini Pro vision call. Mocked in tests."""
    if not settings.GEMINI_API_KEY:
        log.warning("GEMINI_API_KEY missing; queueing image")
        return ""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        log.error("google-genai not installed for image moderation")
        return ""

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=getattr(settings, "GEMINI_VISION_MODEL", "gemini-2.5-pro"),
        contents=[
            VISION_PROMPT,
            types.Part.from_bytes(data=image_bytes, mime_type=mime or "image/jpeg"),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VISION_RESPONSE_SCHEMA,
            temperature=0.1,
            max_output_tokens=300,
        ),
    )
    return response.text or ""


def moderate_image(
    image_bytes: bytes, *, mime: str = "image/jpeg",
) -> ModerationResult:
    """Run full image moderation pipeline. Fail-closed at every layer."""
    det = deterministic_image_check(image_bytes, mime=mime)
    if det is not None:
        return det

    if not settings.GEMINI_API_KEY:
        return ModerationResult(
            allowed=False, categories=["unconfigured"], severity=2,
            reason="image classifier unconfigured", action="queue",
        )

    try:
        raw = _call_gemini_vision(image_bytes, mime)
    except Exception:  # noqa: BLE001
        log.exception("Gemini vision call failed")
        return ModerationResult(
            allowed=False, categories=["upstream_error"], severity=3,
            reason="vision classifier error", action="queue",
        )

    parsed = _parse_vision_response(raw)
    return ModerationResult(
        allowed=bool(parsed.get("allowed", False)),
        categories=list(parsed.get("categories", ["malformed_response"])),
        severity=int(parsed.get("severity", 3)),
        reason=str(parsed.get("reason", "")),
        action=str(parsed.get("action", "queue")),
    )
