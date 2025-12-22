"""
Golden tests for TableNormalizer.

Validates that the table normalizer produces expected output for known inputs,
ensuring deterministic behavior and correct pattern matching across formats.
"""

import sys
from pathlib import Path

# Add src to path for imports
TESTS_DIR = Path(__file__).parent
PRODUCT_ROOT = TESTS_DIR.parent
SRC_DIR = PRODUCT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from ninobyte_context_cleaner import PIIRedactor, TableNormalizer


class TestTableNormalizerGolden:
    """Golden test suite for TableNormalizer."""

    GOLDENS_DIR = TESTS_DIR / "goldens"

    def _process_with_normalize(self, text: str) -> str:
        """Apply PII redaction then table normalization (matches CLI order)."""
        redactor = PIIRedactor()
        normalizer = TableNormalizer()
        result = redactor.redact(text)
        result = normalizer.normalize(result)
        return result

    def test_golden_pipe_table(self):
        """
        Golden test: pipe-delimited table normalization.

        Verifies:
        - Pipe tables are detected and converted
        - PII in table cells is redacted
        - Surrounding text is preserved
        """
        input_path = self.GOLDENS_DIR / "table_pipe_input.txt"
        expected_path = self.GOLDENS_DIR / "table_pipe_expected.txt"

        input_text = input_path.read_text(encoding="utf-8")
        expected_output = expected_path.read_text(encoding="utf-8")

        actual_output = self._process_with_normalize(input_text)

        assert actual_output == expected_output, (
            f"Pipe table golden test failed.\n"
            f"Expected:\n{expected_output}\n"
            f"Actual:\n{actual_output}"
        )

    def test_golden_csv_table(self):
        """
        Golden test: CSV-style table normalization.

        Verifies:
        - Comma-separated tables are detected and converted
        - PII in table cells is redacted
        - Surrounding text is preserved
        """
        input_path = self.GOLDENS_DIR / "table_csv_input.txt"
        expected_path = self.GOLDENS_DIR / "table_csv_expected.txt"

        input_text = input_path.read_text(encoding="utf-8")
        expected_output = expected_path.read_text(encoding="utf-8")

        actual_output = self._process_with_normalize(input_text)

        assert actual_output == expected_output, (
            f"CSV table golden test failed.\n"
            f"Expected:\n{expected_output}\n"
            f"Actual:\n{actual_output}"
        )

    def test_golden_tsv_table(self):
        """
        Golden test: TSV-style table normalization.

        Verifies:
        - Tab-separated tables are detected and converted
        - PII in table cells is redacted
        - Surrounding text is preserved
        """
        input_path = self.GOLDENS_DIR / "table_tsv_input.txt"
        expected_path = self.GOLDENS_DIR / "table_tsv_expected.txt"

        input_text = input_path.read_text(encoding="utf-8")
        expected_output = expected_path.read_text(encoding="utf-8")

        actual_output = self._process_with_normalize(input_text)

        assert actual_output == expected_output, (
            f"TSV table golden test failed.\n"
            f"Expected:\n{expected_output}\n"
            f"Actual:\n{actual_output}"
        )

    def test_noop_without_flag(self):
        """
        Verify that table content is NOT normalized when flag is off.

        When --normalize-tables is not used, tables should pass through
        with only PII redaction applied.
        """
        input_text = """\
| Name | Email |
|------|-------|
| John | john@example.com |
"""
        # Only redact, don't normalize
        redactor = PIIRedactor()
        output = redactor.redact(input_text)

        # Table structure should be preserved (pipes still present)
        assert "|" in output, "Table structure should be preserved without --normalize-tables"
        assert "Name" in output, "Header should be preserved"
        assert "[EMAIL_REDACTED]" in output, "PII should still be redacted"

    def test_determinism(self):
        """Verify that table normalization is deterministic."""
        input_text = """\
| Col1 | Col2 |
|------|------|
| a    | b    |
| c    | d    |
"""
        normalizer = TableNormalizer()

        # Run multiple times
        outputs = [normalizer.normalize(input_text) for _ in range(5)]

        # All outputs must be identical
        assert all(o == outputs[0] for o in outputs), (
            "Table normalization is not deterministic: outputs differ across runs"
        )

    def test_plain_text_unchanged(self):
        """Verify that plain text without tables passes through unchanged."""
        input_text = "This is just plain text.\nNo tables here.\nJust sentences."

        normalizer = TableNormalizer()
        output = normalizer.normalize(input_text)

        assert output == input_text, (
            f"Plain text was modified by normalizer.\n"
            f"Input: {input_text}\n"
            f"Output: {output}"
        )

    def test_short_csv_not_matched(self):
        """Verify that single CSV-like lines are not treated as tables."""
        # A single line with commas should not become a table
        input_text = "The values are: a, b, c\n"

        normalizer = TableNormalizer()
        output = normalizer.normalize(input_text)

        # Should pass through unchanged (no Row 1: prefix)
        assert "Row 1:" not in output, (
            f"Single comma line was incorrectly treated as table.\n"
            f"Output: {output}"
        )

    def test_mixed_content(self):
        """Test document with both tables and regular text."""
        input_text = """\
Introduction paragraph.

| Header1 | Header2 |
|---------|---------|
| value1  | value2  |

Middle paragraph.

Another sentence here.
"""
        normalizer = TableNormalizer()
        output = normalizer.normalize(input_text)

        # Table should be normalized
        assert "Row 1: Header1=value1, Header2=value2" in output
        # Paragraphs should be preserved
        assert "Introduction paragraph." in output
        assert "Middle paragraph." in output
        assert "Another sentence here." in output
