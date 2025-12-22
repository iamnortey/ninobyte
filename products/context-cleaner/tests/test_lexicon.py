"""
Tests for lexicon injection feature (Phase 2.3B).

These tests enforce:
1. Deterministic replacement behavior
2. Reserved token protection
3. Path security
4. JSONL schema v1 contract preservation
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


class TestLexiconGoldenJsonl:
    """Golden test: stdin → jsonl with lexicon enabled."""

    def test_lexicon_jsonl_golden(self):
        """
        Golden test: stdin → jsonl with lexicon enabled.

        Asserts EXACT line match including:
        - Key order preserved (meta, normalized, redacted)
        - meta.lexicon object present with correct structure
        - schema_version = "1" preserved
        """
        lexicon_path = GOLDENS_DIR / "test_lexicon.json"
        expected_file = GOLDENS_DIR / "schema_v1_lexicon_expected.jsonl"
        expected = expected_file.read_text(encoding="utf-8").strip()

        stdout, stderr, code = run_cli(
            ["--output-format", "jsonl", "--lexicon", str(lexicon_path)],
            stdin_text="Visit NYC and contact Acme Inc today!\n"
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        actual = stdout.strip()

        # EXACT line match - not just parsed equivalence
        assert actual == expected, (
            f"Lexicon JSONL contract violation: output does not match golden.\n"
            f"Expected:\n{expected}\n\n"
            f"Actual:\n{actual}\n\n"
            f"Diff analysis: Key order or field values may differ."
        )


class TestLexiconDeterminism:
    """Determinism test: same input + lexicon run 3x identical."""

    def test_lexicon_deterministic_output(self):
        """
        Verify lexicon output is deterministic across multiple runs.
        Same input + lexicon must produce byte-identical output.
        """
        lexicon_path = GOLDENS_DIR / "test_lexicon.json"
        input_text = "Visit NYC and contact Acme Inc today!\n"

        outputs = []
        for _ in range(3):
            stdout, _, code = run_cli(
                ["--output-format", "jsonl", "--lexicon", str(lexicon_path)],
                stdin_text=input_text
            )
            assert code == 0
            outputs.append(stdout)

        # All outputs must be byte-identical
        assert all(o == outputs[0] for o in outputs), (
            "Lexicon output is not deterministic across runs"
        )


class TestLexiconOverlapRule:
    """Overlap rule test: longer keys are replaced first."""

    def test_lexicon_overlap_longer_first(self):
        """
        Test overlap rule: keys {"New York": "NY", "New": "Old"}.

        "New York" should be replaced first (longer key), leaving
        "New" only to match standalone occurrences.

        Input: "New York is a New place"
        Expected: "NY is a Old place"
        """
        lexicon_path = GOLDENS_DIR / "overlap_lexicon.json"
        input_text = "New York is a New place\n"

        stdout, stderr, code = run_cli(
            ["--lexicon", str(lexicon_path)],
            stdin_text=input_text
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        # "New York" → "NY" first, then "New" → "Old"
        expected = "NY is a Old place\n"
        assert stdout == expected, (
            f"Overlap rule violation.\n"
            f"Expected: {expected!r}\n"
            f"Actual: {stdout!r}"
        )


class TestLexiconPathSecurity:
    """Path traversal security tests."""

    def test_lexicon_path_traversal_blocked(self):
        """
        Path traversal must be blocked for --lexicon.
        Attempting to use ../../../etc/passwd should exit 2.
        """
        stdout, stderr, code = run_cli(
            ["--lexicon", "../../../etc/passwd"],
            stdin_text="test\n"
        )

        assert code == 2, (
            f"Path traversal should exit 2, got {code}. Stderr: {stderr}"
        )
        assert "not allowed" in stderr.lower() or "traversal" in stderr.lower(), (
            f"Error message should mention path traversal. Stderr: {stderr}"
        )

    def test_lexicon_nonexistent_file_blocked(self):
        """
        Nonexistent lexicon file should exit 2.
        """
        stdout, stderr, code = run_cli(
            ["--lexicon", "/nonexistent/path/lexicon.json"],
            stdin_text="test\n"
        )

        assert code == 2, (
            f"Nonexistent file should exit 2, got {code}. Stderr: {stderr}"
        )
        assert "not found" in stderr.lower(), (
            f"Error message should mention file not found. Stderr: {stderr}"
        )


class TestLexiconReservedTokenProtection:
    """Reserved token protection tests."""

    def test_reserved_token_protection(self):
        """
        Reserved tokens like [EMAIL_REDACTED] must remain untouched
        after lexicon injection.

        Lexicon rule: {"EMAIL": "Electronic Mail"}
        Input containing "[EMAIL_REDACTED]" must stay exactly as-is.
        """
        # Create a lexicon that would match part of a reserved token
        import tempfile
        import os

        lexicon_content = {
            "EMAIL": "Electronic Mail",
            "PHONE": "Telephone"
        }

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump(lexicon_content, f)
            lexicon_path = f.name

        try:
            input_text = "Contact [EMAIL_REDACTED] or [PHONE_REDACTED]\n"

            stdout, stderr, code = run_cli(
                ["--lexicon", lexicon_path],
                stdin_text=input_text
            )

            assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

            # Reserved tokens must remain exactly as-is
            assert "[EMAIL_REDACTED]" in stdout, (
                f"Reserved token [EMAIL_REDACTED] was modified. Output: {stdout}"
            )
            assert "[PHONE_REDACTED]" in stdout, (
                f"Reserved token [PHONE_REDACTED] was modified. Output: {stdout}"
            )
        finally:
            os.unlink(lexicon_path)

    def test_reserved_token_exact_match(self):
        """
        Verify reserved tokens are protected exactly as-is.
        Input with "[EMAIL_REDACTED]" must output exactly "[EMAIL_REDACTED]".
        """
        import tempfile
        import os

        # Lexicon with a key that's a substring of reserved token
        lexicon_content = {"REDACTED": "REMOVED"}

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        ) as f:
            json.dump(lexicon_content, f)
            lexicon_path = f.name

        try:
            input_text = "[EMAIL_REDACTED] should stay\n"

            stdout, stderr, code = run_cli(
                ["--lexicon", lexicon_path],
                stdin_text=input_text
            )

            assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

            # The exact reserved token must be preserved
            expected = "[EMAIL_REDACTED] should stay\n"
            assert stdout == expected, (
                f"Reserved token protection failed.\n"
                f"Expected: {expected!r}\n"
                f"Actual: {stdout!r}"
            )
        finally:
            os.unlink(lexicon_path)


class TestLexiconSchemaV1Preservation:
    """Verify schema v1 contract is preserved with lexicon."""

    def test_schema_v1_key_order_with_lexicon(self):
        """
        Verify top-level key order: meta, normalized, redacted
        is preserved when lexicon is enabled.
        """
        lexicon_path = GOLDENS_DIR / "test_lexicon.json"

        stdout, stderr, code = run_cli(
            ["--output-format", "jsonl", "--lexicon", str(lexicon_path)],
            stdin_text="test\n"
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        raw = stdout.strip()

        # Find positions of top-level keys
        meta_pos = raw.find('"meta"')
        normalized_pos = raw.find('"normalized"')
        redacted_pos = raw.find('"redacted"')

        assert meta_pos < normalized_pos < redacted_pos, (
            f"Top-level key order violation with lexicon.\n"
            f"Positions: meta={meta_pos}, normalized={normalized_pos}, "
            f"redacted={redacted_pos}"
        )

    def test_schema_version_preserved_with_lexicon(self):
        """
        Verify schema_version is "1" when lexicon is enabled.
        """
        lexicon_path = GOLDENS_DIR / "test_lexicon.json"

        stdout, stderr, code = run_cli(
            ["--output-format", "jsonl", "--lexicon", str(lexicon_path)],
            stdin_text="test\n"
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        data = json.loads(stdout.strip())
        assert data["meta"]["schema_version"] == "1", (
            f"schema_version must be '1'. Got: {data['meta']['schema_version']!r}"
        )


class TestLexiconCLIFlags:
    """Tests for lexicon CLI flags."""

    def test_lexicon_mode_invalid(self):
        """Invalid --lexicon-mode should exit 2."""
        lexicon_path = GOLDENS_DIR / "test_lexicon.json"

        stdout, stderr, code = run_cli(
            ["--lexicon", str(lexicon_path), "--lexicon-mode", "invalid"],
            stdin_text="test\n"
        )

        assert code == 2, f"Invalid mode should exit 2, got {code}"
        assert "invalid" in stderr.lower(), f"Should mention invalid mode: {stderr}"

    def test_lexicon_target_invalid(self):
        """Invalid --lexicon-target should exit 2."""
        lexicon_path = GOLDENS_DIR / "test_lexicon.json"

        stdout, stderr, code = run_cli(
            ["--lexicon", str(lexicon_path), "--lexicon-target", "invalid"],
            stdin_text="test\n"
        )

        assert code == 2, f"Invalid target should exit 2, got {code}"
        assert "invalid" in stderr.lower(), f"Should mention invalid target: {stderr}"

    def test_lexicon_target_normalized(self):
        """
        Test --lexicon-target normalized only applies to normalized stream.
        """
        lexicon_path = GOLDENS_DIR / "test_lexicon.json"
        input_text = "| Place | Info |\n|-------|------|\n| NYC | Visit! |\n"

        stdout, stderr, code = run_cli(
            [
                "--normalize-tables",
                "--lexicon", str(lexicon_path),
                "--lexicon-target", "normalized",
                "--output-format", "jsonl"
            ],
            stdin_text=input_text
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        data = json.loads(stdout.strip())

        # normalized stream should have lexicon applied
        assert "New York City" in data["normalized"], (
            f"Lexicon not applied to normalized. Got: {data['normalized']}"
        )

        # redacted stream uses original input (lexicon NOT applied to input)
        # But wait - redacted comes from input_text, which didn't have lexicon
        # applied when target=normalized
        assert "NYC" in data["redacted"], (
            f"Lexicon should NOT apply to redacted when target=normalized. "
            f"Got: {data['redacted']}"
        )
