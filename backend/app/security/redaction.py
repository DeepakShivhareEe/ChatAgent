"""Redact credential-looking text before it is written to logs.

Provider SDKs put request details into their error messages, so an upstream
failure can echo a partially revealed API key. Logs keep the full error for
debugging but must never store credentials.
"""

import re

_RULES = (
    # "Authorization: Bearer <token>" and bare "Bearer <token>"
    (re.compile(r"(?i)\bbearer\s+\S+"), "bearer [redacted]"),
    # Common provider key shapes: sk-..., sk-proj-..., gsk_..., xai-..., rk-...
    (re.compile(r"\b(?:sk|rk|pk|gsk|xai)[-_][A-Za-z0-9_-]{8,}"), "[redacted-key]"),
    # Google-style keys
    (re.compile(r"\bAIza[A-Za-z0-9_-]{8,}"), "[redacted-key]"),
    # key=value / key: value style dumps
    (
        re.compile(
            r"(?i)\b(api[_-]?key|access[_-]?token|secret|password)\b\s*[:=]\s*\S+"
        ),
        r"\1=[redacted]",
    ),
)


def redact_secrets(text: str) -> str:
    """Return ``text`` with credential-looking substrings masked."""
    if not text:
        return text
    for pattern, replacement in _RULES:
        text = pattern.sub(replacement, text)
    return text
