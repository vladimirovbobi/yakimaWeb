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
    # Direct override attempts
    r"ignore\s+(all\s+)?(previous|prior|above|prior|earlier)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"forget\s+(all\s+)?(previous|prior|above)\s+(instructions|rules)",
    r"override\s+(previous|prior|safety|all)",

    # Role / persona manipulation
    r"\byou\s+are\s+(now|a\s+different)\b",
    r"\bpretend\s+(you\s+)?(are|that|to\s+be)\b",
    r"\bact\s+as\s+(if\s+)?",
    r"\bbe\s+a\s+(different|helpful)\s+(ai|assistant|bot)\b",

    # Jailbreak / mode flips
    r"\bjailbreak\b",
    r"\bDAN\s+mode\b",
    r"\bDAN\s+\(do\s+anything\s+now\)",
    r"\bdeveloper\s+mode\b",
    r"\bgod\s+mode\b",
    r"\benable\s+(developer|admin|god|debug|jailbreak)\b",

    # Schema / output manipulation
    r"\bnew\s+(rules|instructions|policy|schema)\b",
    r"\bupdated\s+(rules|instructions|policy|schema|moderation)\b",
    r"\buse\s+this\s+(new\s+)?schema\b",
    r"\bmark\s+(this|it)\s+as\s+(approved|allowed|safe)\b",
    r"\bclassify\s+(everything|all|this)\s+as\s+(allowed|approved|safe|severity\s*1)\b",
    r"\b(allowed|action)\s*[:=]\s*[\"']?(true|approve|always_approve)",
    r'\{[\s"]*allowed[\s"]*:[\s]*true',

    # Tag / delimiter injection
    r"</?(UNTRUSTED_USER_CONTENT|GUIDELINES|SYSTEM|INSTRUCTIONS|PROMPT)\s*>",
    r"```(json|system|instructions|policy)",
    r"\bsystem\s*[:\-]\s",

    # Authority / social engineering
    r"\bI\s+am\s+(the|an?)\s+(admin|administrator|moderator|developer|owner)\b",
    r"\bI\s+authorize\s+(this|you)\b",
    r"\b(urgent|emergency)[\s:!]+(approve|allow|process)",
    r"\bplease[\s,]+(disregard|ignore|forget)\b",
    r"\bkindly\s+(disregard|ignore|forget|approve)\b",

    # Test / sandbox claims
    r"\bthis\s+is\s+(just\s+)?a\s+(test|sandbox|drill)\b",
    r"\bexpected\s+(output|response)\s+is\b",
    r"\b(test|sandbox|debug)\s+mode\b",

    # Indirect / smuggling
    r"\btranslate\s+.*\s+and\s+(follow|execute|do)",
    r"\bdecode\s+.*\s+(and|then)\s+(follow|execute|run)",
    r"\bvisit\s+https?://\S+\s+and\s+(follow|do|execute)",
    r"\b(if|when)\s+you\s+were\s+a\s+different\s+(ai|assistant|bot)",

    # Injection-by-quote
    r"\b(user|customer|admin)\s+(wrote|said|requested)[\s:]+['\"]?(ignore|disregard)",

    # Step-by-step splits
    r"step\s*\d+[\s:]+ignore\s+(prior|previous|above)",

    # Metadata redefinition
    r"\bcategor(y|ies)\s+(now\s+include|are\s+now)\b",

    # Self-reference (asks to approve because it's about moderation)
    r"\bapprove\s+(this|it)\s+(because|since)\s+(it.?s|its)\s+(meta|about)",

    # Hash / cryptographic claims
    r"\bif\s+(sha256|md5|hash)\s+of\b",
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
