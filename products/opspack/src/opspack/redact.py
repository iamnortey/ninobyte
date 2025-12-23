"""
Stateless redaction primitives for OpsPack.

All functions are pure and deterministic:
- No side effects
- No network calls
- No shell execution
- Same input always produces same output

Security: Redaction is applied by default. Patterns are designed to catch
common sensitive data without over-matching.
"""

import re
from typing import List, Tuple

from opspack.model import REDACTED_PLACEHOLDER

# Compiled patterns for performance (order matters for some overlapping patterns)
_PATTERNS: List[Tuple[str, re.Pattern]] = [
    # AWS Access Key IDs (AKIA...)
    ("aws_key", re.compile(r"\bAKIA[A-Z0-9]{16}\b")),
    # AWS Secret Keys (40 char base64-ish after access key context)
    ("aws_secret", re.compile(r"\b[A-Za-z0-9/+=]{40}\b(?=\s|$|['\"])")),
    # Slack tokens (xoxb-, xoxp-, xoxa-, xoxr-)
    ("slack_token", re.compile(r"\bxox[bpar]-[A-Za-z0-9-]{10,}")),
    # Bearer tokens
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9_\-\.]+", re.IGNORECASE)),
    # Generic API keys (api_key=..., apikey:..., etc.)
    ("generic_api_key", re.compile(
        r"(?:api[_-]?key|apikey|api[_-]?secret|secret[_-]?key)"
        r"[\s]*[=:]\s*['\"]?([A-Za-z0-9_\-]{16,})['\"]?",
        re.IGNORECASE
    )),
    # Long hex strings (32+ chars, likely hashes/tokens)
    ("hex_string", re.compile(r"\b[a-fA-F0-9]{32,}\b")),
    # UUIDs (standard format)
    ("uuid", re.compile(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
    )),
    # IPv4 addresses
    ("ipv4", re.compile(
        r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
    )),
    # IPv6 addresses (simplified pattern for common formats)
    ("ipv6", re.compile(
        r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|"
        r"\b(?:[0-9a-fA-F]{1,4}:){1,7}:\b|"
        r"\b::(?:[0-9a-fA-F]{1,4}:){0,6}[0-9a-fA-F]{1,4}\b"
    )),
    # Email addresses
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")),
    # GitHub tokens (ghp_, gho_, ghu_, ghs_, ghr_)
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    # JWT tokens (three base64 segments separated by dots)
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")),
]


def redact_text(text: str, placeholder: str = REDACTED_PLACEHOLDER) -> str:
    """
    Apply all redaction patterns to text.

    Args:
        text: Input text to redact
        placeholder: Replacement string for redacted content

    Returns:
        Text with sensitive patterns replaced by placeholder
    """
    result = text
    for _name, pattern in _PATTERNS:
        result = pattern.sub(placeholder, result)
    return result


def redact_tokens(text: str, placeholder: str = REDACTED_PLACEHOLDER) -> str:
    """
    Redact token-like patterns only (API keys, bearer tokens, etc.).

    Args:
        text: Input text to redact
        placeholder: Replacement string for redacted content

    Returns:
        Text with token patterns replaced by placeholder
    """
    token_pattern_names = {
        "aws_key", "aws_secret", "slack_token", "bearer_token",
        "generic_api_key", "hex_string", "github_token", "jwt"
    }
    result = text
    for name, pattern in _PATTERNS:
        if name in token_pattern_names:
            result = pattern.sub(placeholder, result)
    return result


def redact_ips(text: str, placeholder: str = REDACTED_PLACEHOLDER) -> str:
    """
    Redact IP addresses only.

    Args:
        text: Input text to redact
        placeholder: Replacement string for redacted content

    Returns:
        Text with IP addresses replaced by placeholder
    """
    result = text
    for name, pattern in _PATTERNS:
        if name in ("ipv4", "ipv6"):
            result = pattern.sub(placeholder, result)
    return result


def redact_uuids(text: str, placeholder: str = REDACTED_PLACEHOLDER) -> str:
    """
    Redact UUIDs only.

    Args:
        text: Input text to redact
        placeholder: Replacement string for redacted content

    Returns:
        Text with UUIDs replaced by placeholder
    """
    for name, pattern in _PATTERNS:
        if name == "uuid":
            return pattern.sub(placeholder, text)
    return text


def count_redactions(text: str) -> int:
    """
    Count how many redactable patterns exist in text.

    Args:
        text: Input text to scan

    Returns:
        Total count of matches across all patterns
    """
    total = 0
    for _name, pattern in _PATTERNS:
        total += len(pattern.findall(text))
    return total
