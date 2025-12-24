"""
CompliancePack Redaction Module.

Provides deterministic typed redaction for excerpts.

Redaction tokens:
- [REDACTED_KEY] for access keys/tokens
- [REDACTED_EMAIL] for email addresses
- [REDACTED_TOKEN] for private key markers and other sensitive tokens
- [REDACTED] for generic sensitive content

Default: Redaction ON
Opt-out: --no-redact flag
"""

import re
from typing import Optional


# Redaction patterns with their replacement tokens
# Order matters: more specific patterns first
REDACTION_PATTERNS = [
    # AWS Access Key pattern
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED_KEY]"),
    # AWS Secret Key pattern (40 char base64-ish)
    (re.compile(r"[A-Za-z0-9/+=]{40}"), "[REDACTED_KEY]"),
    # Private key markers
    (re.compile(r"-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----"), "[REDACTED_TOKEN]"),
    (re.compile(r"-----END\s+(?:RSA\s+)?PRIVATE\s+KEY-----"), "[REDACTED_TOKEN]"),
    (re.compile(r"BEGIN\s+PRIVATE\s+KEY"), "[REDACTED_TOKEN]"),
    (re.compile(r"END\s+PRIVATE\s+KEY"), "[REDACTED_TOKEN]"),
    # Email addresses
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[REDACTED_EMAIL]"),
    # Generic API key patterns
    (re.compile(r"api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_-]{16,}['\"]?", re.IGNORECASE), "[REDACTED_KEY]"),
    (re.compile(r"secret\s*[:=]\s*['\"]?[A-Za-z0-9_-]{16,}['\"]?", re.IGNORECASE), "[REDACTED_KEY]"),
]


def redact_text(text: str, apply_redaction: bool = True) -> str:
    """
    Apply redaction to text.

    Args:
        text: Text to redact
        apply_redaction: If False, return text unchanged

    Returns:
        Redacted text (or original if apply_redaction=False)
    """
    if not apply_redaction:
        return text

    result = text
    for pattern, replacement in REDACTION_PATTERNS:
        result = pattern.sub(replacement, result)

    return result


def create_excerpt(
    line: str,
    col_start: int,
    col_end: int,
    max_length: int = 120,
    apply_redaction: bool = True,
) -> str:
    """
    Create a deterministic excerpt from a line.

    Args:
        line: The full line of text
        col_start: Start column of the match (0-indexed)
        col_end: End column of the match (0-indexed, exclusive)
        max_length: Maximum excerpt length
        apply_redaction: Whether to apply redaction

    Returns:
        Excerpt string, possibly truncated and redacted
    """
    # Calculate window around match
    match_length = col_end - col_start
    padding = (max_length - match_length) // 2

    # Determine excerpt boundaries
    start = max(0, col_start - padding)
    end = min(len(line), col_end + padding)

    # Ensure we don't exceed max_length
    if end - start > max_length:
        end = start + max_length

    excerpt = line[start:end]

    # Add ellipsis indicators if truncated
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(line) else ""

    # Build final excerpt
    result = f"{prefix}{excerpt}{suffix}"

    # Apply redaction if enabled
    return redact_text(result, apply_redaction)


def redact_match_value(
    value: str,
    policy_type: str,
    apply_redaction: bool = True,
) -> str:
    """
    Redact a matched value based on policy type.

    Args:
        value: The matched value
        policy_type: "regex" or "contains"
        apply_redaction: Whether to apply redaction

    Returns:
        Redacted value (or original if apply_redaction=False)
    """
    if not apply_redaction:
        return value

    return redact_text(value, apply_redaction)
