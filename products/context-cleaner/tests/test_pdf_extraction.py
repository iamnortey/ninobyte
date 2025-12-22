"""
Tests for PDF text extraction.

Validates:
- PDF text extraction with PII redaction
- Auto-detection of .pdf extension
- Explicit --input-type pdf
- Missing dependency error handling
- Path traversal security for PDF files
- JSONL output with PDF metadata

NOTE: Tests requiring pypdf will SKIP (not fail) if pypdf is not installed.
This allows core CI to run without optional extras.
The "ContextCleaner PDF Tests" CI job installs [pdf] extras to run these tests.
"""

import json
import subprocess
import sys
import unittest.mock
from pathlib import Path

import pytest

# Skip entire module if pypdf is not available
# This allows core CI (without extras) to safely skip PDF tests
pypdf = pytest.importorskip("pypdf", reason="pypdf required for PDF tests")

# Test directories
TESTS_DIR = Path(__file__).parent
PRODUCT_ROOT = TESTS_DIR.parent
SRC_DIR = PRODUCT_ROOT / "src"
GOLDENS_DIR = TESTS_DIR / "goldens"


def run_cli(args: list, stdin_text: str = "", env_override: dict = None) -> tuple:
    """
    Run the context-cleaner CLI with given args and stdin.

    Args:
        args: CLI arguments
        stdin_text: Input text for stdin
        env_override: Environment variable overrides

    Returns:
        (stdout, stderr, return_code)
    """
    import os
    env = {"PYTHONPATH": str(SRC_DIR), **dict(os.environ)}
    if env_override:
        env.update(env_override)

    cmd = [sys.executable, "-m", "ninobyte_context_cleaner"] + args
    result = subprocess.run(
        cmd,
        input=stdin_text,
        capture_output=True,
        text=True,
        cwd=str(SRC_DIR),
        env=env
    )
    return result.stdout, result.stderr, result.returncode


class TestPDFExtraction:
    """Tests for PDF text extraction."""

    def test_pdf_extraction_basic(self):
        """Test basic PDF extraction with PII redaction."""
        pdf_file = GOLDENS_DIR / "sample_contact.pdf"
        expected_file = GOLDENS_DIR / "sample_contact_expected.txt"

        expected = expected_file.read_text(encoding="utf-8")

        stdout, stderr, code = run_cli(["--input", str(pdf_file)])

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"
        assert stdout == expected, (
            f"PDF extraction output mismatch.\n"
            f"Expected:\n{expected}\n"
            f"Actual:\n{stdout}"
        )

    def test_pdf_auto_detection(self):
        """Test that .pdf extension triggers PDF mode automatically."""
        pdf_file = GOLDENS_DIR / "sample_contact.pdf"

        stdout, stderr, code = run_cli(["--input", str(pdf_file)])

        assert code == 0, f"Auto-detection failed. Stderr: {stderr}"
        assert "[EMAIL_REDACTED]" in stdout
        assert "[PHONE_REDACTED]" in stdout

    def test_pdf_explicit_input_type(self):
        """Test explicit --input-type pdf flag."""
        pdf_file = GOLDENS_DIR / "sample_contact.pdf"

        stdout, stderr, code = run_cli([
            "--input", str(pdf_file),
            "--input-type", "pdf"
        ])

        assert code == 0, f"Explicit PDF mode failed. Stderr: {stderr}"
        assert "[EMAIL_REDACTED]" in stdout

    def test_pdf_jsonl_output(self):
        """Test PDF extraction with JSONL output format."""
        pdf_file = GOLDENS_DIR / "sample_contact.pdf"

        stdout, stderr, code = run_cli([
            "--input", str(pdf_file),
            "--output-format", "jsonl"
        ])

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        data = json.loads(stdout.strip())

        # Verify structure
        assert "redacted" in data
        assert "meta" in data
        assert data["meta"]["source"] == "pdf"
        assert data["meta"]["input_type"] == "pdf"
        assert "[EMAIL_REDACTED]" in data["redacted"]

    def test_pdf_deterministic(self):
        """Verify PDF extraction is deterministic."""
        pdf_file = GOLDENS_DIR / "sample_contact.pdf"

        outputs = []
        for _ in range(3):
            stdout, _, code = run_cli(["--input", str(pdf_file)])
            assert code == 0
            outputs.append(stdout)

        assert all(o == outputs[0] for o in outputs), (
            "PDF extraction is not deterministic"
        )


class TestPDFPathSecurity:
    """Tests for path traversal prevention with PDF files."""

    def test_pdf_path_traversal_rejected(self):
        """Test that path traversal is rejected for PDF files."""
        traversal_paths = [
            "../../../etc/passwd.pdf",
            "foo/../../../secret.pdf",
        ]

        for path in traversal_paths:
            stdout, stderr, code = run_cli([
                "--input", path,
                "--input-type", "pdf"
            ])

            assert code == 2, (
                f"Expected exit 2 for path traversal '{path}', got {code}"
            )
            assert "traversal" in stderr.lower() or "not allowed" in stderr.lower(), (
                f"Expected traversal error for '{path}'. Stderr: {stderr}"
            )


class TestPDFInputTypeValidation:
    """Tests for input type validation."""

    def test_input_type_pdf_requires_input_path(self):
        """Test that --input-type pdf requires --input."""
        stdout, stderr, code = run_cli(
            ["--input-type", "pdf"],
            stdin_text="some text"
        )

        assert code == 2, f"Expected exit 2, got {code}"
        assert "requires --input" in stderr

    def test_invalid_input_type(self):
        """Test error for invalid input type."""
        stdout, stderr, code = run_cli(
            ["--input-type", "binary"],
            stdin_text="test"
        )

        assert code == 2, f"Expected exit 2, got {code}"
        assert "Invalid input type" in stderr

    def test_invalid_pdf_mode(self):
        """Test error for invalid PDF mode."""
        pdf_file = GOLDENS_DIR / "sample_contact.pdf"

        stdout, stderr, code = run_cli([
            "--input", str(pdf_file),
            "--pdf-mode", "ocr"
        ])

        assert code == 2, f"Expected exit 2, got {code}"
        assert "Invalid PDF mode" in stderr


class TestPDFMissingDependency:
    """Tests for missing pypdf dependency handling."""

    def test_missing_pdf_dependency_error(self):
        """Test clear error message when pypdf is not installed."""
        # We simulate missing pypdf by patching the import check
        pdf_file = GOLDENS_DIR / "sample_contact.pdf"

        # Create a subprocess with a modified environment that hides pypdf
        # We use a Python script that patches the import
        test_script = '''
import sys
import unittest.mock

# Block pypdf import
sys.modules['pypdf'] = None

# Now import and test
sys.path.insert(0, "{src_dir}")
from ninobyte_context_cleaner.pdf_extractor import is_pdf_available, get_pdf_import_error

# Reset the cache
import ninobyte_context_cleaner.pdf_extractor as mod
mod._PYPDF_AVAILABLE = None

# Check that it reports unavailable
assert not is_pdf_available(), "Should report PDF unavailable"
error_msg = get_pdf_import_error()
assert "pip install" in error_msg, f"Should have install instructions: {{error_msg}}"
assert "[pdf]" in error_msg, f"Should mention [pdf] extra: {{error_msg}}"
print("PASS: Missing dependency handled correctly")
'''.format(src_dir=str(SRC_DIR))

        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, (
            f"Missing dependency test failed.\n"
            f"Stdout: {result.stdout}\n"
            f"Stderr: {result.stderr}"
        )
        assert "PASS" in result.stdout


class TestPDFWithNormalization:
    """Tests for PDF extraction combined with table normalization."""

    def test_pdf_with_normalize_tables(self):
        """Test PDF extraction with table normalization enabled."""
        pdf_file = GOLDENS_DIR / "sample_contact.pdf"

        stdout, stderr, code = run_cli([
            "--input", str(pdf_file),
            "--normalize-tables"
        ])

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"
        # The sample PDF has no tables, so output should be same as without normalization
        assert "[EMAIL_REDACTED]" in stdout

    def test_pdf_jsonl_with_normalize_tables(self):
        """Test PDF + JSONL + normalization combined."""
        pdf_file = GOLDENS_DIR / "sample_contact.pdf"

        stdout, stderr, code = run_cli([
            "--input", str(pdf_file),
            "--normalize-tables",
            "--output-format", "jsonl"
        ])

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        data = json.loads(stdout.strip())

        assert data["meta"]["normalize_tables"] is True
        assert data["meta"]["input_type"] == "pdf"
        # normalized may or may not be null depending on content
