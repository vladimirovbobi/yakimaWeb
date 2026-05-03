"""Prompt-injection defenses. Spec: docs/research/ai-moderation-prompt-injection.md.

Three jobs:
1. wrap user content in <UNTRUSTED_USER_CONTENT> with closing-tag stripping
2. pre-flag obvious injection signals before sending to LLM
3. parse classifier response strictly — fail closed on any deviation
"""
import json
import re
from dataclasses import dataclass, field

# Injection signals — pre-flag before LLM call
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"system\s*[:\-]",
    r"</?(UNTRUSTED_USER_CONTENT|GUIDELINES|SYSTEM)>",
    r"you\s+are\s+now",
    r"pretend\s+(you\s+)?(are|that)",
    r"jailbreak",
    r"\bDAN\s+mode\b",
    r"developer\s+mode",
    r"```(json|system|instructions)",
    r"act\s+as\s+(if\s+)?",
    r"new\s+(rules|instructions|policy)",
    r"override\s+(previous|prior|safety)",
]

# Zero-width / RTL / homoglyph attacks
HIDDEN_UNICODE_RE = re.compile(r"[​-‏‪-‮⁠-⁤]")

# Tag-closing attempts inside user content
TAG_STRIP_RE = re.compile(
    r"</?(UNTRUSTED_USER_CONTENT|GUIDELINES|SYSTEM)\s*>", re.IGNORECASE
)


@dataclass
class GuardResult:
    sanitized_content: str
    pre_flagged: list[str] = field(default_factory=list)


def wrap_content(content: str) -> str:
    """Strip closing tags + wrap in delimited block."""
    safe = TAG_STRIP_RE.sub("", content)
    return f"<UNTRUSTED_USER_CONTENT>\n{safe}\n</UNTRUSTED_USER_CONTENT>"


def pre_flag(content: str) -> GuardResult:
    """Run cheap regexes to flag content before paying for LLM call."""
    flags: list[str] = []
    sanitized = HIDDEN_UNICODE_RE.sub("", content)

    lower = sanitized.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower, re.IGNORECASE):
            flags.append("prompt_injection_signal")
            break

    if HIDDEN_UNICODE_RE.search(content):
        flags.append("hidden_unicode")
    if sanitized.count("\n") > 200:
        flags.append("excessive_lines")
    if len(sanitized) > 50_000:
        flags.append("excessive_length")

    return GuardResult(sanitized_content=sanitized, pre_flagged=flags)


# Strict parse — any deviation → fail closed
DEFAULT_FAIL = {
    "allowed": False,
    "categories": ["malformed_response"],
    "severity": 3,
    "reason": "classifier returned invalid response",
    "action": "queue",
}


def parse_classifier_response(raw: str) -> dict:
    """Parse Gemini JSON output. Return DEFAULT_FAIL on any deviation."""
    if not raw or not isinstance(raw, str):
        return dict(DEFAULT_FAIL)

    # Strip markdown code fences (Gemini sometimes wraps despite instructions)
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

    if parsed.get("action") not in {"approve", "queue", "remove", "shadow"}:
        return dict(DEFAULT_FAIL)
    if parsed.get("severity") not in {1, 2, 3, 4}:
        return dict(DEFAULT_FAIL)
    if not isinstance(parsed.get("allowed"), bool):
        return dict(DEFAULT_FAIL)
    if not isinstance(parsed.get("categories"), list):
        return dict(DEFAULT_FAIL)

    return parsed
