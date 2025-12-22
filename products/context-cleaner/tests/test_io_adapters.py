"""
Tests for IO adapters: file input and JSONL output.

Validates:
- File input mode (--input)
- JSONL output format (--output-format jsonl)
- Path traversal security (reject ".." paths)
"""

import json
import subprocess
import sys
from pathlib import Path

# Test directories
TESTS_DIR = Path(__file__).parent
PRODUCT_ROOT = TESTS_DIR.parent
SRC_DIR = PRODUCT_ROOT / "src"
GOLDENS_DIR = TESTS_DIR / "goldens"


def run_cli(args: list, stdin_text: str = "") -> tuple:
    """
    Run the context-cleaner CLI with given args and stdin.

    Returns:
        (stdout, stderr, return_code)
    """
    cmd = [sys.executable, "-m", "ninobyte_context_cleaner"] + args
    result = subprocess.run(
        cmd,
        input=stdin_text,
        capture_output=True,
        text=True,
        cwd=str(SRC_DIR),
        env={"PYTHONPATH": str(SRC_DIR), **dict(__import__("os").environ)}
    )
    return result.stdout, result.stderr, result.returncode


class TestFileInput:
    """Tests for --input file read mode."""

    def test_file_input_basic(self):
        """Test reading from a file instead of stdin."""
        input_file = GOLDENS_DIR / "file_input_sample.txt"
        expected_file = GOLDENS_DIR / "file_input_expected.txt"

        expected = expected_file.read_text(encoding="utf-8")

        stdout, stderr, code = run_cli(["--input", str(input_file)])

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"
        assert stdout == expected, (
            f"File input output mismatch.\n"
            f"Expected:\n{expected}\n"
            f"Actual:\n{stdout}"
        )

    def test_file_not_found(self):
        """Test error handling for missing file."""
        stdout, stderr, code = run_cli(["--input", "/nonexistent/file.txt"])

        assert code == 2, f"Expected exit 2 for missing file, got {code}"
        assert "File not found" in stderr or "not found" in stderr.lower()

    def test_directory_rejected(self):
        """Test that directories are rejected as input."""
        stdout, stderr, code = run_cli(["--input", str(TESTS_DIR)])

        assert code == 2, f"Expected exit 2 for directory input, got {code}"
        assert "Not a file" in stderr


class TestPathSecurity:
    """Tests for path traversal prevention."""

    def test_path_traversal_rejected(self):
        """Test that path traversal attempts are rejected."""
        # Test Unix-style traversal patterns (cross-platform on path normalization)
        traversal_paths = [
            "../../../etc/passwd",
            "foo/../../../etc/passwd",
        ]

        for path in traversal_paths:
            stdout, stderr, code = run_cli(["--input", path])

            assert code == 2, (
                f"Expected exit 2 for path traversal '{path}', got {code}"
            )
            assert "traversal" in stderr.lower() or "not allowed" in stderr.lower(), (
                f"Expected traversal error message for '{path}'. Stderr: {stderr}"
            )

    def test_relative_path_without_traversal_allowed(self):
        """Test that relative paths without traversal are allowed."""
        # This test uses a file that exists in the goldens directory
        input_file = GOLDENS_DIR / "file_input_sample.txt"

        stdout, stderr, code = run_cli(["--input", str(input_file)])

        assert code == 0, f"Relative path should work. Stderr: {stderr}"


class TestJsonlOutput:
    """Tests for --output-format jsonl."""

    def test_jsonl_basic(self):
        """Test basic JSONL output format."""
        stdout, stderr, code = run_cli(
            ["--output-format", "jsonl"],
            stdin_text="Contact test@example.com\n"
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        # Parse the JSON output
        data = json.loads(stdout.strip())

        # Verify structure
        assert "redacted" in data
        assert "normalized" in data
        assert "meta" in data
        assert data["meta"]["source"] == "stdin"
        assert data["meta"]["normalize_tables"] is False
        assert data["meta"]["version"] == "0.1.0"
        assert data["normalized"] is None  # No normalization requested
        assert "[EMAIL_REDACTED]" in data["redacted"]

    def test_jsonl_with_normalize_tables(self):
        """Test JSONL output with table normalization enabled."""
        input_text = "| Name | Email |\n|------|-------|\n| John | john@test.com |\n"

        stdout, stderr, code = run_cli(
            ["--output-format", "jsonl", "--normalize-tables"],
            stdin_text=input_text
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        data = json.loads(stdout.strip())

        assert data["meta"]["normalize_tables"] is True
        assert data["normalized"] is not None
        assert "Row 1:" in data["normalized"]
        assert "[EMAIL_REDACTED]" in data["normalized"]

    def test_jsonl_from_file(self):
        """Test JSONL output with file input."""
        input_file = GOLDENS_DIR / "file_input_sample.txt"

        stdout, stderr, code = run_cli(
            ["--input", str(input_file), "--output-format", "jsonl"]
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        data = json.loads(stdout.strip())

        assert data["meta"]["source"] == "file"
        assert "[EMAIL_REDACTED]" in data["redacted"]
        assert "[PHONE_REDACTED]" in data["redacted"]

    def test_jsonl_deterministic(self):
        """Verify JSONL output is deterministic (same input -> same output)."""
        input_text = "test@example.com 555-123-4567\n"

        outputs = []
        for _ in range(3):
            stdout, _, code = run_cli(
                ["--output-format", "jsonl"],
                stdin_text=input_text
            )
            assert code == 0
            outputs.append(stdout)

        # All outputs must be identical
        assert all(o == outputs[0] for o in outputs), (
            "JSONL output is not deterministic"
        )

    def test_invalid_output_format(self):
        """Test error handling for invalid output format."""
        stdout, stderr, code = run_cli(
            ["--output-format", "xml"],
            stdin_text="test\n"
        )

        assert code == 2, f"Expected exit 2 for invalid format, got {code}"
        assert "Invalid output format" in stderr


class TestCombinedOptions:
    """Tests for combined CLI options."""

    def test_file_input_with_jsonl_and_normalize(self):
        """Test all options combined: file input, JSONL output, normalization."""
        input_file = GOLDENS_DIR / "table_pipe_input.txt"

        stdout, stderr, code = run_cli([
            "--input", str(input_file),
            "--output-format", "jsonl",
            "--normalize-tables"
        ])

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        data = json.loads(stdout.strip())

        assert data["meta"]["source"] == "file"
        assert data["meta"]["normalize_tables"] is True
        assert data["normalized"] is not None
        assert "Row 1:" in data["normalized"] or "Row 2:" in data["normalized"]

    def test_text_output_still_default(self):
        """Verify text output is still the default."""
        stdout, stderr, code = run_cli(
            [],  # No flags
            stdin_text="test@example.com\n"
        )

        assert code == 0
        # Should be plain text, not JSON
        assert "[EMAIL_REDACTED]" in stdout
        assert "{" not in stdout  # Not JSON
