"""Layer 1 — deterministic, no-LLM checks. Cheap, fast, runs first."""
import hashlib
import re
from dataclasses import dataclass

# Tunable thresholds
MAX_LENGTH = 50_000
MIN_LENGTH = 1
MAX_LINKS_DENSE = 5
DENSE_LENGTH_THRESHOLD = 500
MAX_LINKS_TOTAL = 25

URL_RE   = re.compile(r"https?://\S+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_RE = re.compile(r"(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}")
SCRIPT_RE = re.compile(r"<\s*script", re.IGNORECASE)

# Replace with a real list — placeholder for now
KNOWN_BAD_TERMS: set[str] = set()


@dataclass
class DetermResult:
    blocked: bool = False
    queue: bool = False
    reason: str = ""
    flags: list[str] = None

    def __post_init__(self):
        if self.flags is None:
            self.flags = []


def hash_input(content: str) -> str:
    """SHA-256 of normalized content for replay/dedup detection."""
    norm = re.sub(r"\s+", " ", content.strip().lower())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def deterministic_check(content: str, *, context: str = "default") -> DetermResult:
    """Run all Layer 1 checks. Returns first match."""
    if not content or len(content) < MIN_LENGTH:
        return DetermResult(blocked=True, reason="empty_content")
    if len(content) > MAX_LENGTH:
        return DetermResult(blocked=True, reason="excessive_length")

    if SCRIPT_RE.search(content):
        return DetermResult(blocked=True, reason="injection_html_script")

    urls = URL_RE.findall(content)
    if len(urls) > MAX_LINKS_TOTAL:
        return DetermResult(blocked=True, reason="excessive_links")
    if len(urls) > MAX_LINKS_DENSE and len(content) < DENSE_LENGTH_THRESHOLD:
        return DetermResult(queue=True, reason="dense_link_spam_suspect",
                           flags=["dense_links"])

    if context in {"comment", "forum_reply"}:
        if EMAIL_RE.search(content) or PHONE_RE.search(content):
            return DetermResult(queue=True, reason="contact_info_in_public_thread",
                               flags=["personal_info"])

    lower = content.lower()
    for term in KNOWN_BAD_TERMS:
        if term in lower:
            return DetermResult(queue=True, reason=f"known_bad_term:{term[:8]}",
                               flags=["bad_word"])

    return DetermResult()
