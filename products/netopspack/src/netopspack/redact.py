"""
Redaction utilities for sensitive data in network logs.

Patterns redacted:
- IPv4 addresses
- IPv6 addresses
- Bearer tokens
- JWT-like tokens (three dot-separated base64url segments)
- API keys (api_key=..., apikey:..., etc.)
- Generic long base64-ish tokens
- Email addresses
- AWS access keys (AKIA..., ASIA...)
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


# Redaction patterns - ORDER MATTERS (more specific patterns first)
# Patterns are applied sequentially, so we need to ensure:
# 1. IPv4/IPv6 first (specific IP formats)
# 2. JWT before generic base64 (JWT is more specific 3-segment format)
# 3. Bearer tokens
# 4. API keys
# 5. AWS keys (specific prefix)
# 6. Email
# 7. Generic tokens last (catches remaining long base64-ish strings)
# 8. Long hex last (broadest pattern)

PATTERNS = {
    # IPv4: Standard dotted-quad notation
    "ipv4": (
        re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        "[REDACTED_IP]",
    ),
    # IPv6: Multiple formats (full, compressed, mixed)
    "ipv6": (
        re.compile(
            r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|"
            r"\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b|"
            r"\b(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}\b|"
            r"\b::(?:[0-9a-fA-F]{1,4}:){0,5}[0-9a-fA-F]{1,4}\b|"
            r"\b(?:[0-9a-fA-F]{1,4}:){1,5}::[0-9a-fA-F]{1,4}\b"
        ),
        "[REDACTED_IP]",
    ),
    # JWT-like: Three base64url-encoded segments separated by dots
    # Header.Payload.Signature format (each segment 4+ chars of base64url)
    "jwt": (
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{3,}\.[A-Za-z0-9_-]{4,}\.[A-Za-z0-9_-]{4,}\b"
        ),
        "[REDACTED_TOKEN]",
    ),
    # Bearer token with value
    "bearer": (
        re.compile(r"Bearer\s+[A-Za-z0-9\-_\.]+", re.IGNORECASE),
        "Bearer [REDACTED_TOKEN]",
    ),
    # API key in various formats: api_key=..., api-key:..., apikey="..."
    "api_key": (
        re.compile(
            r"(?:api[_-]?key|apikey)\s*[=:]\s*['\"]?[\w\-]+['\"]?",
            re.IGNORECASE,
        ),
        "api_key=[REDACTED_KEY]",
    ),
    # AWS Access Key IDs: AKIA... (long-term) and ASIA... (temporary/STS)
    "aws_key": (
        re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
        "[REDACTED_AWS_KEY]",
    ),
    # Email addresses
    "email": (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
    # Generic long base64-ish tokens (40+ chars of base64 alphabet)
    # This catches API tokens, secrets, etc. that don't match other patterns
    "generic_token": (
        re.compile(r"\b[A-Za-z0-9+/=_-]{40,}\b"),
        "[REDACTED_TOKEN]",
    ),
    # Long hex strings (32+ chars) - common for session IDs, hashes, etc.
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

    # Apply each pattern - order is important (defined in PATTERNS dict)
    for pattern_name, (pattern, replacement) in PATTERNS.items():
        matches = pattern.findall(result)
        if matches and stats is not None:
            if pattern_name in ("ipv4", "ipv6"):
                stats.ips += len(matches)
            elif pattern_name in ("bearer", "jwt", "generic_token"):
                stats.tokens += len(matches)
            elif pattern_name == "api_key":
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
