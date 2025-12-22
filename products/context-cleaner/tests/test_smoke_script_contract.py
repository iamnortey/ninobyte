"""
Tests for smoke harness functions.

Unit-tests the smoke harness WITHOUT requiring pdf extras.
Verifies smoke harness can run and pass core checks in-process.
Ensures schema v1 contract tests remain intact.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add scripts directory to path for import
TESTS_DIR = Path(__file__).parent
PRODUCT_ROOT = TESTS_DIR.parent
SCRIPTS_DIR = PRODUCT_ROOT / "scripts"
SRC_DIR = PRODUCT_ROOT / "src"

# Ensure src is in path for imports
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from smoke_context_cleaner import (
    capture_cli,
    test_stdin_jsonl_key_order,
    test_normalized_explicit_null,
    test_normalized_string_with_tables,
    test_lexicon_meta_present,
    test_reserved_token_protection,
    test_path_traversal_rejected,
    test_determinism,
    SmokeResult,
)


class TestCaptureCliInfrastructure:
    """Tests for the capture_cli helper function."""

    def test_capture_cli_returns_tuple(self):
        """capture_cli returns (stdout, stderr, code) tuple."""
        result = capture_cli(["--version"])

        assert isinstance(result, tuple)
        assert len(result) == 3
        stdout, stderr, code = result
        assert isinstance(stdout, str)
        assert isinstance(stderr, str)
        assert isinstance(code, int)

    def test_capture_cli_version_flag(self):
        """--version returns version string and exit 0."""
        stdout, stderr, code = capture_cli(["--version"])

        assert code == 0
        assert "ninobyte-context-cleaner" in stdout
        assert stderr == ""

    def test_capture_cli_help_flag(self):
        """--help returns usage and exit 0."""
        stdout, stderr, code = capture_cli(["--help"])

        assert code == 0
        assert "Usage:" in stdout

    def test_capture_cli_stdin_passthrough(self):
        """stdin text is passed to CLI."""
        stdout, stderr, code = capture_cli(
            ["--output-format", "jsonl"],
            stdin_text="hello world\n"
        )

        assert code == 0
        data = json.loads(stdout.strip())
        assert "redacted" in data
        assert "hello world" in data["redacted"]

    def test_capture_cli_error_exit_code(self):
        """Invalid args return exit code 2."""
        stdout, stderr, code = capture_cli(["--invalid-flag"])

        assert code == 2
        assert "Unknown option" in stderr or "error" in stderr.lower()


class TestSmokeTestFunctions:
    """Tests for individual smoke test functions."""

    def test_stdin_jsonl_key_order_passes(self):
        """test_stdin_jsonl_key_order returns PASS."""
        result = test_stdin_jsonl_key_order()

        assert isinstance(result, SmokeResult)
        assert result.passed, f"Expected PASS, got: {result.message}"

    def test_normalized_explicit_null_passes(self):
        """test_normalized_explicit_null returns PASS."""
        result = test_normalized_explicit_null()

        assert result.passed, f"Expected PASS, got: {result.message}"

    def test_normalized_string_with_tables_passes(self):
        """test_normalized_string_with_tables returns PASS."""
        result = test_normalized_string_with_tables()

        assert result.passed, f"Expected PASS, got: {result.message}"

    def test_lexicon_meta_present_passes(self):
        """test_lexicon_meta_present returns PASS."""
        result = test_lexicon_meta_present()

        assert result.passed, f"Expected PASS, got: {result.message}"

    def test_reserved_token_protection_passes(self):
        """test_reserved_token_protection returns PASS."""
        result = test_reserved_token_protection()

        assert result.passed, f"Expected PASS, got: {result.message}"

    def test_path_traversal_rejected_passes(self):
        """test_path_traversal_rejected returns PASS."""
        result = test_path_traversal_rejected()

        assert result.passed, f"Expected PASS, got: {result.message}"

    def test_determinism_passes(self):
        """test_determinism returns PASS."""
        result = test_determinism()

        assert result.passed, f"Expected PASS, got: {result.message}"


class TestSchemaV1ContractPreserved:
    """Verify schema v1 contract is preserved by smoke harness tests."""

    def test_schema_version_is_string_one(self):
        """schema_version must be "1" (string, not integer)."""
        stdout, _, code = capture_cli(
            ["--output-format", "jsonl"],
            stdin_text="test\n"
        )

        assert code == 0
        data = json.loads(stdout.strip())

        assert data["meta"]["schema_version"] == "1"
        assert isinstance(data["meta"]["schema_version"], str)

    def test_toplevel_key_order_preserved(self):
        """Top-level keys: meta → normalized → redacted."""
        stdout, _, code = capture_cli(
            ["--output-format", "jsonl"],
            stdin_text="test\n"
        )

        assert code == 0
        raw = stdout.strip()

        meta_pos = raw.find('"meta"')
        normalized_pos = raw.find('"normalized"')
        redacted_pos = raw.find('"redacted"')

        assert meta_pos < normalized_pos < redacted_pos

    def test_meta_key_order_preserved(self):
        """Meta keys: schema_version, version, source, input_type, normalize_tables."""
        stdout, _, code = capture_cli(
            ["--output-format", "jsonl"],
            stdin_text="test\n"
        )

        assert code == 0
        raw = stdout.strip()

        required = ["schema_version", "version", "source", "input_type", "normalize_tables"]
        positions = {key: raw.find(f'"{key}"') for key in required}

        # Verify order
        for i in range(len(required) - 1):
            curr_key = required[i]
            next_key = required[i + 1]
            assert positions[curr_key] < positions[next_key], (
                f"Meta key order violation: {curr_key} should appear before {next_key}"
            )

    def test_normalized_always_present(self):
        """normalized key is always present (explicit null or string)."""
        # Without normalize-tables (should be null)
        stdout1, _, code1 = capture_cli(
            ["--output-format", "jsonl"],
            stdin_text="test\n"
        )
        assert code1 == 0
        data1 = json.loads(stdout1.strip())
        assert "normalized" in data1

        # With normalize-tables (should be string)
        stdout2, _, code2 = capture_cli(
            ["--output-format", "jsonl", "--normalize-tables"],
            stdin_text="| A | B |\n|---|---|\n| 1 | 2 |\n"
        )
        assert code2 == 0
        data2 = json.loads(stdout2.strip())
        assert "normalized" in data2

    def test_redacted_always_string(self):
        """redacted is always a string."""
        stdout, _, code = capture_cli(
            ["--output-format", "jsonl"],
            stdin_text="test@example.com\n"
        )

        assert code == 0
        data = json.loads(stdout.strip())

        assert "redacted" in data
        assert isinstance(data["redacted"], str)
