"""
Redaction utilities for sensitive data in network logs.

Patterns redacted:
- IPv4 addresses
- IPv6 addresses
- Bearer tokens
- API keys
- Email addresses
- AWS access keys
- Long hex strings (32+ chars)
"""

import re
from dataclasses import dataclass


@dataclass
class RedactionStats:
    """Statistics about redactions performed."""

    ips: int = 0
    tokens: int = 0
    emails: int = 0
    keys: int = 0
    hex_strings: int = 0


# Redaction patterns
PATTERNS = {
    "ipv4": (
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        "[REDACTED_IP]",
    ),
    "ipv6": (
        re.compile(
            r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|"
            r"\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b|"
            r"\b(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}\b|"
            r"\b::(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}\b"
        ),
        "[REDACTED_IP]",
    ),
    "bearer": (
        re.compile(r"Bearer\s+[A-Za-z0-9\-_\.]+", re.IGNORECASE),
        "Bearer [REDACTED_TOKEN]",
    ),
    "api_key": (
        re.compile(r"(?:api[_-]?key|apikey)\s*[=:]\s*['\"]?[\w\-]+['\"]?", re.IGNORECASE),
        "api_key=[REDACTED_KEY]",
    ),
    "email": (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
    "aws_key": (
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "[REDACTED_AWS]",
    ),
    "long_hex": (
        re.compile(r"\b[0-9a-fA-F]{32,}\b"),
        "[REDACTED_HEX]",
    ),
}


def redact_line(line: str, stats: RedactionStats | None = None) -> str:
    """
    Redact sensitive patterns from a single line.

    Args:
        line: The line to redact
        stats: Optional stats object to track redaction counts

    Returns:
        The redacted line
    """
    result = line

    # Apply each pattern
    for pattern_name, (pattern, replacement) in PATTERNS.items():
        matches = pattern.findall(result)
        if matches and stats is not None:
            if pattern_name in ("ipv4", "ipv6"):
                stats.ips += len(matches)
            elif pattern_name in ("bearer", "api_key"):
                stats.tokens += len(matches)
            elif pattern_name == "email":
                stats.emails += len(matches)
            elif pattern_name == "aws_key":
                stats.keys += len(matches)
            elif pattern_name == "long_hex":
                stats.hex_strings += len(matches)

        result = pattern.sub(replacement, result)

    return result


def redact_text(text: str) -> tuple[str, RedactionStats]:
    """
    Redact sensitive patterns from text.

    Args:
        text: The text to redact

    Returns:
        Tuple of (redacted text, redaction statistics)
    """
    stats = RedactionStats()
    lines = text.split("\n")
    redacted_lines = [redact_line(line, stats) for line in lines]
    return "\n".join(redacted_lines), stats
