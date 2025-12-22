"""
Golden test for PIIRedactor.

Validates that the redactor produces expected output for a known input,
ensuring deterministic behavior and correct pattern matching.
"""

import sys
from pathlib import Path

# Add src to path for imports
TESTS_DIR = Path(__file__).parent
PRODUCT_ROOT = TESTS_DIR.parent
SRC_DIR = PRODUCT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from ninobyte_context_cleaner import PIIRedactor


class TestPIIRedactorGolden:
    """Golden test suite for PIIRedactor."""

    GOLDENS_DIR = TESTS_DIR / "goldens"

    def test_golden_pii_redaction(self):
        """
        Golden test: verify redactor output matches expected for known input.

        This test ensures:
        1. Email addresses are redacted
        2. Phone numbers (various formats) are redacted
        3. Non-PII text is preserved
        4. Output is deterministic
        """
        input_path = self.GOLDENS_DIR / "pii_input.txt"
        expected_path = self.GOLDENS_DIR / "pii_expected.txt"

        input_text = input_path.read_text(encoding="utf-8")
        expected_output = expected_path.read_text(encoding="utf-8")

        redactor = PIIRedactor()
        actual_output = redactor.redact(input_text)

        assert actual_output == expected_output, (
            f"Golden test failed.\n"
            f"Expected:\n{expected_output}\n"
            f"Actual:\n{actual_output}"
        )

    def test_determinism(self):
        """Verify that redaction is deterministic (same input -> same output)."""
        input_text = "Contact john@example.com or call 555-123-4567"

        redactor = PIIRedactor()

        # Run multiple times
        outputs = [redactor.redact(input_text) for _ in range(5)]

        # All outputs must be identical
        assert all(o == outputs[0] for o in outputs), (
            "Redaction is not deterministic: outputs differ across runs"
        )

    def test_year_not_redacted(self):
        """Verify that short numeric sequences like years are NOT redacted."""
        input_text = "The year 2025 should remain unchanged."

        redactor = PIIRedactor()
        output = redactor.redact(input_text)

        assert "2025" in output, (
            f"Year '2025' was incorrectly redacted. Output: {output}"
        )

    def test_email_redaction(self):
        """Verify email addresses are properly redacted."""
        test_cases = [
            ("Contact user@example.com", "Contact [EMAIL_REDACTED]"),
            ("Email: test.user+tag@sub.domain.co.uk", "Email: [EMAIL_REDACTED]"),
            ("Multiple: a@b.com and c@d.org", "Multiple: [EMAIL_REDACTED] and [EMAIL_REDACTED]"),
        ]

        redactor = PIIRedactor()

        for input_text, expected in test_cases:
            actual = redactor.redact(input_text)
            assert actual == expected, (
                f"Email redaction failed.\n"
                f"Input: {input_text}\n"
                f"Expected: {expected}\n"
                f"Actual: {actual}"
            )

    def test_phone_redaction_various_formats(self):
        """Verify phone numbers in various formats are redacted."""
        test_cases = [
            # 10+ digits always redacted
            ("Call 5551234567", "Call [PHONE_REDACTED]"),
            ("Number: 15551234567", "Number: [PHONE_REDACTED]"),
            # Formatted phone numbers
            ("Call (555) 123-4567", "Call [PHONE_REDACTED]"),
            ("Call 555-123-4567", "Call [PHONE_REDACTED]"),
            ("Call 555.123.4567", "Call [PHONE_REDACTED]"),
            ("Call 1-800-555-0199", "Call [PHONE_REDACTED]"),
            ("Call +1 555 123 4567", "Call [PHONE_REDACTED]"),
        ]

        redactor = PIIRedactor()

        for input_text, expected in test_cases:
            actual = redactor.redact(input_text)
            assert actual == expected, (
                f"Phone redaction failed.\n"
                f"Input: {input_text}\n"
                f"Expected: {expected}\n"
                f"Actual: {actual}"
            )

    def test_no_false_positives_short_numbers(self):
        """Verify short numeric sequences are NOT redacted as phones."""
        test_cases = [
            "The year 2025 is coming",
            "Room 101 is available",
            "Order #12345 confirmed",
            "Version 1.2.3 released",
        ]

        redactor = PIIRedactor()

        for input_text in test_cases:
            output = redactor.redact(input_text)
            assert "[PHONE_REDACTED]" not in output, (
                f"False positive: '{input_text}' was incorrectly redacted to '{output}'"
            )
