"""
Ninobyte ContextCleaner - Deterministic PII redaction for LLM context preparation.

This module provides the PIIRedactor class for identifying and replacing
common PII patterns with stable placeholders, and TableNormalizer for
converting table-like content into LLM-friendly text.

Example:
    >>> from ninobyte_context_cleaner import PIIRedactor
    >>> redactor = PIIRedactor()
    >>> redactor.redact("Contact john@example.com")
    'Contact [EMAIL_REDACTED]'

    >>> from ninobyte_context_cleaner import TableNormalizer
    >>> normalizer = TableNormalizer()
    >>> normalizer.normalize("| a | b |\\n| 1 | 2 |")
    'Row 1: a=1, b=2'
"""

from ninobyte_context_cleaner.redactor import PIIRedactor
from ninobyte_context_cleaner.table_normalizer import TableNormalizer
from ninobyte_context_cleaner.version import __version__

__all__ = ["PIIRedactor", "TableNormalizer", "__version__"]
