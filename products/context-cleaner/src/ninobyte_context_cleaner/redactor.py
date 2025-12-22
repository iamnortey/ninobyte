"""
PIIRedactor - Deterministic PII redaction engine.

Provides conservative pattern matching for common PII types:
- Email addresses
- Phone numbers (with careful rules to avoid false positives)
"""

import re
from typing import Pattern


class PIIRedactor:
    """
    Deterministic PII redaction engine.

    Replaces identified PII patterns with stable placeholders.
    Same input always produces same output.
    """

    # Email pattern: standard email format
    # Matches: user@domain.tld, user.name+tag@sub.domain.co.uk
    EMAIL_PATTERN: Pattern[str] = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        re.ASCII
    )

    # Phone pattern: matches phone-like sequences
    # Strategy: Match liberally, then validate in replacement function
    # This pattern captures potential phone numbers for validation
    PHONE_CANDIDATE_PATTERN: Pattern[str] = re.compile(
        r'''
        (?:
            # International format: +1 555 123 4567 or +1-555-123-4567
            \+\d[\d\s.\-]{7,}
            |
            # Parentheses format: (555) 123-4567
            \(\d{3}\)[\s.\-]?\d{3}[\s.\-]?\d{4}
            |
            # Standard formats with separators: 555-123-4567, 555.123.4567
            \d{3}[\s.\-]\d{3}[\s.\-]\d{4}
            |
            # With leading 1: 1-800-555-0199
            1[\s.\-]\d{3}[\s.\-]\d{3}[\s.\-]\d{4}
            |
            # 10+ consecutive digits (no separators): 5551234567
            (?<![a-fA-F0-9])\d{10,}(?![a-fA-F0-9])
            |
            # 7-9 digits with phone formatting signals
            (?:
                \d{3}[\s.\-]\d{4}  # 555-1234
                |
                \d{3}[\s.\-]\d{3}[\s.\-]\d{1,4}  # Various separator patterns
            )
        )
        ''',
        re.VERBOSE
    )

    EMAIL_PLACEHOLDER = "[EMAIL_REDACTED]"
    PHONE_PLACEHOLDER = "[PHONE_REDACTED]"

    def __init__(self) -> None:
        """Initialize the PIIRedactor."""
        pass

    def _count_digits(self, text: str) -> int:
        """Count the number of digit characters in text."""
        return sum(1 for c in text if c.isdigit())

    def _has_phone_format_signals(self, text: str) -> bool:
        """
        Check if text has formatting signals typical of phone numbers.

        Signals include: parentheses, +, dashes between digits, dots between digits,
        spaces between digit groups.
        """
        # Check for explicit phone formatting characters
        if '(' in text or '+' in text:
            return True

        # Check for separators between digit groups (not at edges)
        # Pattern: digit followed by separator followed by digit
        if re.search(r'\d[\s.\-]\d', text):
            return True

        return False

    def _is_valid_phone(self, match: str) -> bool:
        """
        Validate whether a matched string is likely a phone number.

        Rules:
        - If total digits >= 10: valid (standard phone number length)
        - If digits >= 7 AND has phone-format signals: valid
        - Otherwise: not valid (avoid matching years, short IDs, etc.)
        """
        digit_count = self._count_digits(match)

        # 10+ digits is definitely a phone number
        if digit_count >= 10:
            return True

        # 7-9 digits with formatting signals is likely a phone
        if digit_count >= 7 and self._has_phone_format_signals(match):
            return True

        return False

    def _redact_phones(self, text: str) -> str:
        """
        Redact phone numbers from text.

        Uses conservative matching to avoid false positives on:
        - Years (2025)
        - Short numeric IDs
        - Hex strings (Git SHAs)
        """
        def replace_if_valid(match: re.Match[str]) -> str:
            matched_text = match.group(0)
            if self._is_valid_phone(matched_text):
                return self.PHONE_PLACEHOLDER
            return matched_text

        return self.PHONE_CANDIDATE_PATTERN.sub(replace_if_valid, text)

    def redact(self, text: str) -> str:
        """
        Redact PII from text.

        Applies redaction patterns in order:
        1. Email addresses → [EMAIL_REDACTED]
        2. Phone numbers → [PHONE_REDACTED]

        Args:
            text: Input text potentially containing PII

        Returns:
            Text with PII replaced by stable placeholders.
            Output is deterministic: same input always produces same output.
        """
        # Step 1: Redact emails first (they may contain digits)
        result = self.EMAIL_PATTERN.sub(self.EMAIL_PLACEHOLDER, text)

        # Step 2: Redact phone numbers
        result = self._redact_phones(result)

        return result
