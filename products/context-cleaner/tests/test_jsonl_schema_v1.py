"""
Tests for JSONL Schema v1 contract enforcement.

Schema v1 Contract:
- Top-level key order: "meta", "normalized", "redacted"
- meta key order: schema_version, version, source, input_type, normalize_tables
- "normalized" is always present (explicit null if not requested)
- "redacted" is always a string
- schema_version is hardcoded to "1"

These tests enforce EXACT JSON line equality (not just parsed dict equivalence)
to ensure downstream pipelines receive stable, predictable output.
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


class TestJsonlSchemaV1Contract:
    """Tests for JSONL Schema v1 contract enforcement."""

    def test_schema_v1_stdin_golden(self):
        """
        Golden test: stdin → jsonl with simple email input.

        Asserts EXACT line match including:
        - Key order (meta, normalized, redacted)
        - schema_version = "1"
        - Explicit null for normalized
        """
        expected_file = GOLDENS_DIR / "schema_v1_stdin_expected.jsonl"
        expected = expected_file.read_text(encoding="utf-8").strip()

        stdout, stderr, code = run_cli(
            ["--output-format", "jsonl"],
            stdin_text="Contact test@example.com\n"
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        actual = stdout.strip()

        # EXACT line match - not just parsed equivalence
        assert actual == expected, (
            f"Schema v1 contract violation: JSONL output does not match golden.\n"
            f"Expected:\n{expected}\n\n"
            f"Actual:\n{actual}\n\n"
            f"Diff analysis: Key order or field values may differ."
        )

    def test_schema_v1_file_input_golden(self):
        """
        Golden test: file input → jsonl.

        Asserts EXACT line match including:
        - meta.source = "file"
        - meta.input_type = "text"
        """
        input_file = GOLDENS_DIR / "file_input_sample.txt"
        expected_file = GOLDENS_DIR / "schema_v1_file_expected.jsonl"
        expected = expected_file.read_text(encoding="utf-8").strip()

        stdout, stderr, code = run_cli(
            ["--input", str(input_file), "--output-format", "jsonl"]
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        actual = stdout.strip()

        # EXACT line match
        assert actual == expected, (
            f"Schema v1 contract violation: file input JSONL mismatch.\n"
            f"Expected:\n{expected}\n\n"
            f"Actual:\n{actual}"
        )

    def test_schema_v1_explicit_null_normalized(self):
        """
        Explicit-null test: verify "normalized": null is present when
        --normalize-tables is OFF.

        This is a CONTRACT REQUIREMENT: the field must be present with
        explicit null, not omitted.
        """
        stdout, stderr, code = run_cli(
            ["--output-format", "jsonl"],
            stdin_text="test@example.com\n"
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        # Check raw string contains explicit null
        assert '"normalized":null' in stdout, (
            f"Schema v1 contract violation: 'normalized' must be explicit null.\n"
            f"Output: {stdout}"
        )

        # Also verify via parsing
        data = json.loads(stdout.strip())
        assert "normalized" in data, "Key 'normalized' must be present"
        assert data["normalized"] is None, "Value must be None/null"

    def test_schema_v1_key_order_meta(self):
        """
        Verify meta object key order matches contract:
        schema_version, version, source, input_type, normalize_tables
        """
        stdout, stderr, code = run_cli(
            ["--output-format", "jsonl"],
            stdin_text="test\n"
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        # Extract meta portion and verify key order in raw string
        data = json.loads(stdout.strip())
        meta = data["meta"]

        # Keys must exist
        required_keys = ["schema_version", "version", "source", "input_type", "normalize_tables"]
        for key in required_keys:
            assert key in meta, f"Missing required meta key: {key}"

        # Verify order by checking raw string positions
        raw = stdout.strip()
        positions = {key: raw.find(f'"{key}"') for key in required_keys}

        # Each key should appear before the next in the list
        for i in range(len(required_keys) - 1):
            curr_key = required_keys[i]
            next_key = required_keys[i + 1]
            assert positions[curr_key] < positions[next_key], (
                f"Meta key order violation: '{curr_key}' should appear before '{next_key}'"
            )

    def test_schema_v1_key_order_toplevel(self):
        """
        Verify top-level key order matches contract:
        meta, normalized, redacted
        """
        stdout, stderr, code = run_cli(
            ["--output-format", "jsonl"],
            stdin_text="test\n"
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        raw = stdout.strip()

        # Find positions of top-level keys
        meta_pos = raw.find('"meta"')
        normalized_pos = raw.find('"normalized"')
        redacted_pos = raw.find('"redacted"')

        assert meta_pos < normalized_pos < redacted_pos, (
            f"Top-level key order violation. Expected: meta < normalized < redacted.\n"
            f"Positions: meta={meta_pos}, normalized={normalized_pos}, redacted={redacted_pos}"
        )

    def test_schema_v1_schema_version_hardcoded(self):
        """
        Verify schema_version is hardcoded to "1" (string, not integer).
        """
        stdout, stderr, code = run_cli(
            ["--output-format", "jsonl"],
            stdin_text="test\n"
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        data = json.loads(stdout.strip())

        assert data["meta"]["schema_version"] == "1", (
            f"schema_version must be '1' (string). Got: {data['meta']['schema_version']!r}"
        )

        # Also verify it's a string type
        assert isinstance(data["meta"]["schema_version"], str), (
            "schema_version must be a string, not an integer"
        )

    def test_schema_v1_deterministic(self):
        """
        Verify JSONL output is deterministic across multiple runs.
        Same input must produce byte-identical output.
        """
        input_text = "Contact john@example.com or call 555-123-4567\n"

        outputs = []
        for _ in range(3):
            stdout, _, code = run_cli(
                ["--output-format", "jsonl"],
                stdin_text=input_text
            )
            assert code == 0
            outputs.append(stdout)

        # All outputs must be byte-identical
        assert all(o == outputs[0] for o in outputs), (
            "Schema v1 contract violation: output is not deterministic"
        )

    def test_schema_v1_with_normalize_tables(self):
        """
        Verify schema v1 contract when --normalize-tables is enabled.
        normalized field should contain string, not null.
        """
        input_text = "| Name | Email |\n|------|-------|\n| John | john@test.com |\n"

        stdout, stderr, code = run_cli(
            ["--output-format", "jsonl", "--normalize-tables"],
            stdin_text=input_text
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        data = json.loads(stdout.strip())

        # Verify contract fields
        assert data["meta"]["schema_version"] == "1"
        assert data["meta"]["normalize_tables"] is True
        assert data["normalized"] is not None, "normalized should be string when flag enabled"
        assert isinstance(data["normalized"], str)
        assert "[EMAIL_REDACTED]" in data["normalized"]
