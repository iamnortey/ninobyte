"""
redact_preview Tool Implementation

CRITICAL REQUIREMENT: This module MUST remain STATELESS.
- Input: string
- Output: string
- NO file reads
- NO external state
- Pure string transformation only
"""

import re
from dataclasses import dataclass
from typing import List, Pattern, Tuple


# Redaction patterns - compiled once for performance
REDACTION_PATTERNS: List[Tuple[Pattern, str, str]] = [
    # API keys and tokens
    (re.compile(r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?'),
     r'\1=<REDACTED_API_KEY>', 'api_key'),

    # Bearer tokens
    (re.compile(r'(?i)(bearer)\s+([a-zA-Z0-9_\-\.]+)'),
     r'\1 <REDACTED_BEARER_TOKEN>', 'bearer_token'),

    # AWS keys
    (re.compile(r'(?i)(aws[_-]?(?:access[_-]?key[_-]?id|secret[_-]?access[_-]?key))\s*[:=]\s*["\']?([A-Z0-9/+=]{16,})["\']?'),
     r'\1=<REDACTED_AWS_KEY>', 'aws_key'),

    # Generic secrets/passwords
    (re.compile(r'(?i)(password|passwd|pwd|secret|token)\s*[:=]\s*["\']?([^\s"\']{8,})["\']?'),
     r'\1=<REDACTED>', 'password'),

    # Private keys
    (re.compile(r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----[\s\S]*?-----END\s+(?:RSA\s+)?PRIVATE\s+KEY-----'),
     '<REDACTED_PRIVATE_KEY>', 'private_key'),

    # Connection strings with passwords
    (re.compile(r'(?i)((?:mongodb|postgres|mysql|redis|amqp)(?:\+\w+)?://[^:]+:)([^@]+)(@.+)'),
     r'\1<REDACTED>\3', 'connection_string'),

    # JWT tokens (header.payload.signature format)
    (re.compile(r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'),
     '<REDACTED_JWT>', 'jwt'),

    # GitHub tokens
    (re.compile(r'gh[pousr]_[a-zA-Z0-9]{36,}'),
     '<REDACTED_GITHUB_TOKEN>', 'github_token'),

    # Slack tokens
    (re.compile(r'xox[baprs]-[a-zA-Z0-9-]+'),
     '<REDACTED_SLACK_TOKEN>', 'slack_token'),

    # Credit card numbers (basic pattern)
    (re.compile(r'\b(?:\d{4}[- ]?){3}\d{4}\b'),
     '<REDACTED_CARD_NUMBER>', 'credit_card'),

    # SSN (US format)
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
     '<REDACTED_SSN>', 'ssn'),
]


@dataclass
class RedactionResult:
    """Result of redaction operation."""
    original_length: int
    redacted_length: int
    redactions_applied: int
    redaction_types: List[str]
    content: str

    def to_dict(self) -> dict:
        return {
            "original_length": self.original_length,
            "redacted_length": self.redacted_length,
            "redactions_applied": self.redactions_applied,
            "redaction_types": self.redaction_types,
            "content": self.content
        }


def redact_preview(content: str) -> RedactionResult:
    """
    Redact sensitive information from a string.

    THIS FUNCTION IS STATELESS:
    - Takes a string as input
    - Returns a RedactionResult with redacted content
    - Does NOT read any files
    - Does NOT access any external state
    - Pure string transformation only

    Args:
        content: The string content to redact

    Returns:
        RedactionResult with redacted content and metadata
    """
    if not isinstance(content, str):
        raise TypeError("content must be a string")

    original_length = len(content)
    redactions_applied = 0
    redaction_types: List[str] = []
    redacted_content = content

    for pattern, replacement, redaction_type in REDACTION_PATTERNS:
        # Count matches before replacement
        matches = pattern.findall(redacted_content)
        if matches:
            redactions_applied += len(matches)
            if redaction_type not in redaction_types:
                redaction_types.append(redaction_type)

        # Apply replacement
        redacted_content = pattern.sub(replacement, redacted_content)

    return RedactionResult(
        original_length=original_length,
        redacted_length=len(redacted_content),
        redactions_applied=redactions_applied,
        redaction_types=redaction_types,
        content=redacted_content
    )


def redact_preview_simple(content: str) -> str:
    """
    Simple string-to-string redaction.

    STATELESS: str -> str, no side effects.

    Args:
        content: The string content to redact

    Returns:
        Redacted string
    """
    if not isinstance(content, str):
        raise TypeError("content must be a string")

    result = content
    for pattern, replacement, _ in REDACTION_PATTERNS:
        result = pattern.sub(replacement, result)
    return result
