"""
Tests for CLI UX: help output, exit codes, and error handling.

These tests ensure:
1. --help contains key sections (non-brittle checks)
2. Exit code 2 on invalid args, unsafe paths, missing deps
3. Console entrypoint behavior (via module invocation)
4. Stable error message format ("Error: ...")
"""

import subprocess
import sys
from pathlib import Path

# Test directories
TESTS_DIR = Path(__file__).parent
PRODUCT_ROOT = TESTS_DIR.parent
SRC_DIR = PRODUCT_ROOT / "src"


def run_cli(args: list, stdin_text: str = "") -> tuple:
    """
    Run the context-cleaner CLI with given args and stdin.

    Returns:
        (stdout, stderr, return_code)
    """
    import os
    cmd = [sys.executable, "-m", "ninobyte_context_cleaner"] + args
    result = subprocess.run(
        cmd,
        input=stdin_text,
        capture_output=True,
        text=True,
        cwd=str(SRC_DIR),
        env={"PYTHONPATH": str(SRC_DIR), **dict(os.environ)}
    )
    return result.stdout, result.stderr, result.returncode


class TestHelpOutput:
    """Tests for --help output containing key sections."""

    def test_help_contains_usage(self):
        """--help must contain Usage section."""
        stdout, stderr, code = run_cli(["--help"])
        assert code == 0
        assert "Usage:" in stdout

    def test_help_contains_options(self):
        """--help must contain Options section."""
        stdout, stderr, code = run_cli(["--help"])
        assert code == 0
        assert "Options:" in stdout

    def test_help_contains_examples(self):
        """--help must contain Examples section."""
        stdout, stderr, code = run_cli(["--help"])
        assert code == 0
        assert "Examples:" in stdout

    def test_help_contains_exit_codes(self):
        """--help must contain Exit Codes section."""
        stdout, stderr, code = run_cli(["--help"])
        assert code == 0
        assert "Exit Codes:" in stdout

    def test_help_contains_processing_order(self):
        """--help must contain Processing Order section."""
        stdout, stderr, code = run_cli(["--help"])
        assert code == 0
        assert "Processing Order:" in stdout

    def test_help_mentions_stdin_example(self):
        """--help must show stdin usage example."""
        stdout, stderr, code = run_cli(["--help"])
        assert code == 0
        assert "echo" in stdout.lower() or "stdin" in stdout.lower()

    def test_help_mentions_file_input(self):
        """--help must show file input option."""
        stdout, stderr, code = run_cli(["--help"])
        assert code == 0
        assert "--input" in stdout

    def test_help_mentions_pdf(self):
        """--help must mention PDF support."""
        stdout, stderr, code = run_cli(["--help"])
        assert code == 0
        assert "pdf" in stdout.lower()

    def test_help_mentions_jsonl(self):
        """--help must mention JSONL output."""
        stdout, stderr, code = run_cli(["--help"])
        assert code == 0
        assert "jsonl" in stdout.lower()

    def test_help_mentions_lexicon(self):
        """--help must mention lexicon option."""
        stdout, stderr, code = run_cli(["--help"])
        assert code == 0
        assert "--lexicon" in stdout

    def test_help_mentions_normalize_tables(self):
        """--help must mention table normalization."""
        stdout, stderr, code = run_cli(["--help"])
        assert code == 0
        assert "--normalize-tables" in stdout


class TestExitCodes:
    """Tests for exit code behavior."""

    def test_success_exit_code_0(self):
        """Successful execution must exit 0."""
        stdout, stderr, code = run_cli([], stdin_text="test\n")
        assert code == 0

    def test_help_exit_code_0(self):
        """--help must exit 0."""
        stdout, stderr, code = run_cli(["--help"])
        assert code == 0

    def test_version_exit_code_0(self):
        """--version must exit 0."""
        stdout, stderr, code = run_cli(["--version"])
        assert code == 0

    def test_unknown_option_exit_code_2(self):
        """Unknown option must exit 2."""
        stdout, stderr, code = run_cli(["--unknown-flag"])
        assert code == 2

    def test_invalid_output_format_exit_code_2(self):
        """Invalid --output-format must exit 2."""
        stdout, stderr, code = run_cli(
            ["--output-format", "invalid"],
            stdin_text="test\n"
        )
        assert code == 2

    def test_invalid_input_type_exit_code_2(self):
        """Invalid --input-type must exit 2."""
        stdout, stderr, code = run_cli(
            ["--input-type", "invalid"],
            stdin_text="test\n"
        )
        assert code == 2

    def test_invalid_lexicon_mode_exit_code_2(self):
        """Invalid --lexicon-mode must exit 2."""
        stdout, stderr, code = run_cli(
            ["--lexicon", "test.json", "--lexicon-mode", "invalid"],
            stdin_text="test\n"
        )
        assert code == 2

    def test_nonexistent_input_file_exit_code_2(self):
        """Nonexistent --input file must exit 2."""
        stdout, stderr, code = run_cli(
            ["--input", "/nonexistent/path/file.txt"]
        )
        assert code == 2

    def test_path_traversal_exit_code_2(self):
        """Path traversal attempt must exit 2."""
        stdout, stderr, code = run_cli(
            ["--input", "../../../etc/passwd"]
        )
        assert code == 2

    def test_missing_option_value_exit_code_2(self):
        """Option without required value must exit 2."""
        stdout, stderr, code = run_cli(["--input"])
        assert code == 2


class TestErrorMessageFormat:
    """Tests for stable error message format."""

    def test_unknown_option_error_prefix(self):
        """Unknown option error must be prefixed with 'Error:'."""
        stdout, stderr, code = run_cli(["--unknown-flag"])
        assert "Error:" in stderr

    def test_invalid_format_error_prefix(self):
        """Invalid format error must be prefixed with 'Error:'."""
        stdout, stderr, code = run_cli(
            ["--output-format", "invalid"],
            stdin_text="test\n"
        )
        assert "Error:" in stderr

    def test_file_not_found_error_prefix(self):
        """File not found error must be prefixed with 'Error:'."""
        stdout, stderr, code = run_cli(
            ["--input", "/nonexistent/file.txt"]
        )
        assert "Error:" in stderr

    def test_path_traversal_error_prefix(self):
        """Path traversal error must be prefixed with 'Error:'."""
        stdout, stderr, code = run_cli(
            ["--input", "../../../etc/passwd"]
        )
        assert "Error:" in stderr

    def test_error_suggests_help(self):
        """Error messages should suggest --help."""
        stdout, stderr, code = run_cli(["--unknown-flag"])
        assert "--help" in stderr


class TestVersionOutput:
    """Tests for --version output."""

    def test_version_contains_package_name(self):
        """--version should contain package name."""
        stdout, stderr, code = run_cli(["--version"])
        assert code == 0
        assert "ninobyte-context-cleaner" in stdout

    def test_version_contains_version_number(self):
        """--version should contain version number."""
        stdout, stderr, code = run_cli(["--version"])
        assert code == 0
        # Basic version format check (digits and dots)
        import re
        assert re.search(r'\d+\.\d+\.\d+', stdout) is not None


class TestModuleInvocation:
    """Tests for module invocation behavior."""

    def test_module_invocation_works(self):
        """python -m ninobyte_context_cleaner should work."""
        stdout, stderr, code = run_cli([], stdin_text="test\n")
        assert code == 0
        assert "test" in stdout

    def test_module_version_matches(self):
        """Module version should match package version."""
        stdout, stderr, code = run_cli(["--version"])
        assert code == 0
        assert "0.1.0" in stdout  # Current version
