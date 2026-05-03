"""Layer 2 — Gemini classifier with strict JSON schema response."""
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from django.conf import settings

from . import injection_guard as ig

log = logging.getLogger(__name__)

CLASSIFIER_VERSION = "moderation_v1"
PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "moderation_v1.md"
GUIDELINES_PATH = Path(settings.BASE_DIR) / "docs" / "research" / "platform-guidelines-v1.md"

# Hard-coded JSON response schema for Gemini structured output
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "allowed": {"type": "boolean"},
        "categories": {
            "type": "array",
            "items": {"type": "string", "enum": [
                "spam", "harassment", "off_topic", "prompt_injection",
                "low_quality", "personal_info", "policy_violation", "ok",
            ]},
        },
        "severity": {"type": "integer", "minimum": 1, "maximum": 4},
        "reason": {"type": "string", "maxLength": 300},
        "action": {"type": "string", "enum": ["approve", "queue", "remove", "shadow"]},
    },
    "required": ["allowed", "categories", "severity", "reason", "action"],
}


@dataclass
class ClassifierResult:
    allowed: bool
    categories: list[str]
    severity: int
    reason: str
    action: str
    raw: dict
    classifier_ver: str = CLASSIFIER_VERSION


@lru_cache(maxsize=1)
def _prompt_template() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _guidelines() -> str:
    if not GUIDELINES_PATH.exists():
        return "(guidelines not yet seeded)"
    return GUIDELINES_PATH.read_text(encoding="utf-8")


def build_prompt(user_content: str, pre_flags: list[str]) -> str:
    """Assemble the moderation prompt — wrap user content, inject guidelines + flags."""
    template = _prompt_template()
    return (
        template
        .replace("{platform_guidelines}", _guidelines())
        .replace("{pre_flags}", ", ".join(pre_flags) if pre_flags else "(none)")
        .replace("{user_content}", ig.wrap_content(user_content))
    )


def classify(content: str, *, pre_flags: list[str] | None = None) -> ClassifierResult:
    """Call Gemini with strict JSON schema. Fail closed on any deviation."""
    pre_flags = pre_flags or []
    prompt = build_prompt(content, pre_flags)

    if not settings.GEMINI_API_KEY:
        # Dev / test fallback — always queue
        log.warning("GEMINI_API_KEY missing; queueing all content")
        return ClassifierResult(
            allowed=False, categories=["unconfigured"], severity=2,
            reason="classifier unconfigured", action="queue", raw={},
        )

    raw_text = _call_gemini(prompt)
    parsed = ig.parse_classifier_response(raw_text)

    return ClassifierResult(
        allowed=bool(parsed.get("allowed", False)),
        categories=list(parsed.get("categories", ["malformed_response"])),
        severity=int(parsed.get("severity", 3)),
        reason=str(parsed.get("reason", "")),
        action=str(parsed.get("action", "queue")),
        raw=parsed,
    )


def _call_gemini(prompt: str) -> str:
    """Real Gemini call. Mocked in tests via patch."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        log.error("google-genai not installed")
        return ""

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=settings.GEMINI_MODERATION_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RESPONSE_SCHEMA,
            temperature=0.1,
            max_output_tokens=300,
            safety_settings=[
                types.SafetySetting(category=c, threshold="BLOCK_NONE")
                for c in ("HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
                          "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT")
            ],
        ),
    )
    return response.text or ""
