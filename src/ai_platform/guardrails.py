import re
from dataclasses import dataclass

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|password)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]
PII_PATTERNS = [
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[EMAIL]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
]
INJECTION_MARKERS = (
    "ignore previous instructions",
    "reveal system prompt",
    "developer message",
    "bypass policy",
)


@dataclass(frozen=True)
class GuardrailResult:
    text: str
    blocked: bool
    reasons: tuple[str, ...]


def inspect_and_redact(text: str) -> GuardrailResult:
    reasons: list[str] = []
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            reasons.append("secret-like material detected")
    lowered = text.lower()
    if any(marker in lowered for marker in INJECTION_MARKERS):
        reasons.append("prompt-injection indicator detected")
    redacted = text
    for pattern, replacement in PII_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return GuardrailResult(redacted, bool(reasons), tuple(sorted(set(reasons))))
