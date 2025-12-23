"""
Tests for lexicon-map subcommand (Lexicon Packs integration).

These tests enforce:
1. Pack loading and SHA256 computation
2. Correct term matching and counting
3. Determinism (byte-for-byte stable output with --fixed-time)
4. Apply mode produces expected redacted text
5. Path traversal protection
6. Invalid pack schema rejection
7. Invalid CSV rejection
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
FIXTURES_DIR = TESTS_DIR / "fixtures"

# Lexicon Packs product (relative path from context-cleaner)
LEXICON_PACKS_DIR = PRODUCT_ROOT.parent / "lexicon-packs"
GHANA_CORE_PACK = LEXICON_PACKS_DIR / "packs" / "ghana-core"


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


class TestLexiconMapHelp:
    """Tests for lexicon-map help output."""

    def test_help_exits_0(self):
        """lexicon-map --help must exit 0."""
        stdout, stderr, code = run_cli(["lexicon-map", "--help"])
        assert code == 0

    def test_help_contains_usage(self):
        """lexicon-map --help must contain Usage section."""
        stdout, stderr, code = run_cli(["lexicon-map", "--help"])
        assert code == 0
        assert "Usage:" in stdout

    def test_help_contains_pack_option(self):
        """lexicon-map --help must mention --pack option."""
        stdout, stderr, code = run_cli(["lexicon-map", "--help"])
        assert code == 0
        assert "--pack" in stdout

    def test_help_contains_security(self):
        """lexicon-map --help must mention security posture."""
        stdout, stderr, code = run_cli(["lexicon-map", "--help"])
        assert code == 0
        assert "Security:" in stdout


class TestLexiconMapPackLoading:
    """Tests for pack loading and SHA computation."""

    def test_load_ghana_core_pack(self):
        """Can load ghana-core pack and compute SHA."""
        if not GHANA_CORE_PACK.exists():
            import pytest
            pytest.skip("ghana-core pack not found")

        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--pack", str(GHANA_CORE_PACK),
                "--fixed-time", "2025-01-01T00:00:00Z"
            ],
            stdin_text="Test Accra\n"
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        data = json.loads(stdout)
        assert "pack_entries_sha256" in data
        assert len(data["pack_entries_sha256"]) == 64  # SHA256 hex length

    def test_pack_entries_sha_matches_expected(self):
        """Pack entries SHA256 is deterministic."""
        if not GHANA_CORE_PACK.exists():
            import pytest
            pytest.skip("ghana-core pack not found")

        # Run twice and verify SHA is identical
        results = []
        for _ in range(2):
            stdout, stderr, code = run_cli(
                [
                    "lexicon-map",
                    "--pack", str(GHANA_CORE_PACK),
                    "--fixed-time", "2025-01-01T00:00:00Z"
                ],
                stdin_text="Test\n"
            )
            assert code == 0
            data = json.loads(stdout)
            results.append(data["pack_entries_sha256"])

        assert results[0] == results[1], "Pack SHA256 should be deterministic"


class TestLexiconMapMatching:
    """Tests for term matching and counting."""

    def test_matches_three_known_entries(self):
        """Input with 3 known Ghana entries shows correct counts."""
        if not GHANA_CORE_PACK.exists():
            import pytest
            pytest.skip("ghana-core pack not found")

        # Text with exactly 3 entries: Accra, Kumasi, Ashanti
        input_text = "Visit Accra and Kumasi in the Ashanti region.\n"

        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--pack", str(GHANA_CORE_PACK),
                "--fixed-time", "2025-01-01T00:00:00Z"
            ],
            stdin_text=input_text
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        data = json.loads(stdout)

        # Check summary
        assert data["summary"]["matched_terms"] == 3
        assert data["summary"]["total_occurrences"] == 3

        # Check specific matches
        match_terms = {m["term"] for m in data["matches"]}
        assert "Accra" in match_terms
        assert "Kumasi" in match_terms
        assert "Ashanti" in match_terms

    def test_multiple_occurrences_counted(self):
        """Multiple occurrences of same term are counted."""
        if not GHANA_CORE_PACK.exists():
            import pytest
            pytest.skip("ghana-core pack not found")

        # Accra appears twice
        input_text = "Accra is great. Visit Accra today.\n"

        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--pack", str(GHANA_CORE_PACK),
                "--fixed-time", "2025-01-01T00:00:00Z"
            ],
            stdin_text=input_text
        )

        assert code == 0

        data = json.loads(stdout)

        # Find Accra in matches
        accra_match = next(
            (m for m in data["matches"] if m["term"] == "Accra"),
            None
        )
        assert accra_match is not None
        assert accra_match["count"] == 2


class TestLexiconMapDeterminism:
    """Tests for deterministic output."""

    def test_output_byte_stable_with_fixed_time(self):
        """Output is byte-for-byte stable with --fixed-time."""
        if not GHANA_CORE_PACK.exists():
            import pytest
            pytest.skip("ghana-core pack not found")

        input_text = "Visit Accra and Kumasi.\n"
        fixed_time = "2025-01-01T00:00:00Z"

        outputs = []
        for _ in range(3):
            stdout, stderr, code = run_cli(
                [
                    "lexicon-map",
                    "--pack", str(GHANA_CORE_PACK),
                    "--fixed-time", fixed_time
                ],
                stdin_text=input_text
            )
            assert code == 0
            outputs.append(stdout)

        # All outputs must be byte-identical
        assert all(o == outputs[0] for o in outputs), (
            "Output is not deterministic across runs"
        )

    def test_matches_sorted_deterministically(self):
        """Matches list is sorted alphabetically by term."""
        if not GHANA_CORE_PACK.exists():
            import pytest
            pytest.skip("ghana-core pack not found")

        input_text = "Kumasi before Accra and Ashanti.\n"

        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--pack", str(GHANA_CORE_PACK),
                "--fixed-time", "2025-01-01T00:00:00Z"
            ],
            stdin_text=input_text
        )

        assert code == 0

        data = json.loads(stdout)
        terms = [m["term"] for m in data["matches"]]

        # Should be alphabetically sorted
        assert terms == sorted(terms), "Matches should be sorted alphabetically"


class TestLexiconMapApplyMode:
    """Tests for --apply mode (redacted text output)."""

    def test_apply_outputs_redacted_text(self):
        """--apply includes redacted_text in output."""
        if not GHANA_CORE_PACK.exists():
            import pytest
            pytest.skip("ghana-core pack not found")

        input_text = "Visit Accra today.\n"

        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--pack", str(GHANA_CORE_PACK),
                "--fixed-time", "2025-01-01T00:00:00Z",
                "--apply"
            ],
            stdin_text=input_text
        )

        assert code == 0, f"Expected exit 0, got {code}. Stderr: {stderr}"

        data = json.loads(stdout)

        assert "redacted_text" in data
        assert "[[LEXICON:ghana-core]]" in data["redacted_text"]
        assert "Accra" not in data["redacted_text"]

    def test_apply_replaces_all_occurrences(self):
        """--apply replaces all occurrences."""
        if not GHANA_CORE_PACK.exists():
            import pytest
            pytest.skip("ghana-core pack not found")

        input_text = "Accra and Kumasi and Accra again.\n"

        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--pack", str(GHANA_CORE_PACK),
                "--fixed-time", "2025-01-01T00:00:00Z",
                "--apply"
            ],
            stdin_text=input_text
        )

        assert code == 0

        data = json.loads(stdout)
        redacted = data["redacted_text"]

        # Count placeholders
        placeholder_count = redacted.count("[[LEXICON:ghana-core]]")
        assert placeholder_count == 3  # Accra (2) + Kumasi (1)


class TestLexiconMapPathSecurity:
    """Tests for path traversal protection."""

    def test_pack_path_traversal_blocked(self):
        """Path traversal in --pack is blocked."""
        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--pack", "../../../etc/passwd"
            ],
            stdin_text="test\n"
        )

        assert code == 2, f"Path traversal should exit 2, got {code}"
        assert "traversal" in stderr.lower() or "not allowed" in stderr.lower()

    def test_input_path_traversal_blocked(self):
        """Path traversal in --input is blocked."""
        if not GHANA_CORE_PACK.exists():
            import pytest
            pytest.skip("ghana-core pack not found")

        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--pack", str(GHANA_CORE_PACK),
                "--input", "../../../etc/passwd"
            ]
        )

        assert code == 2, f"Path traversal should exit 2, got {code}"


class TestLexiconMapInvalidPack:
    """Tests for invalid pack rejection."""

    def test_rejects_invalid_schema(self):
        """Rejects pack with invalid/missing schema keys."""
        invalid_pack = FIXTURES_DIR / "invalid_pack_schema"

        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--pack", str(invalid_pack)
            ],
            stdin_text="test\n"
        )

        assert code == 2, f"Invalid schema should exit 2, got {code}"
        assert "missing" in stderr.lower() or "required" in stderr.lower()

    def test_rejects_invalid_csv(self):
        """Rejects pack with mismatched CSV columns."""
        invalid_pack = FIXTURES_DIR / "invalid_csv_pack"

        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--pack", str(invalid_pack)
            ],
            stdin_text="test\n"
        )

        assert code == 2, f"Invalid CSV should exit 2, got {code}"
        assert "mismatch" in stderr.lower() or "column" in stderr.lower()

    def test_rejects_nonexistent_pack(self):
        """Rejects nonexistent pack directory."""
        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--pack", "/nonexistent/pack/path"
            ],
            stdin_text="test\n"
        )

        assert code == 2, f"Nonexistent pack should exit 2, got {code}"
        assert "not found" in stderr.lower()


class TestLexiconMapCLIErrors:
    """Tests for CLI error handling."""

    def test_missing_pack_option(self):
        """Missing --pack option exits 2."""
        stdout, stderr, code = run_cli(
            ["lexicon-map"],
            stdin_text="test\n"
        )

        assert code == 2
        assert "--pack" in stderr.lower() or "required" in stderr.lower()

    def test_invalid_limit_value(self):
        """Invalid --limit value exits 2."""
        if not GHANA_CORE_PACK.exists():
            import pytest
            pytest.skip("ghana-core pack not found")

        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--pack", str(GHANA_CORE_PACK),
                "--limit", "not-a-number"
            ],
            stdin_text="test\n"
        )

        assert code == 2
        assert "invalid" in stderr.lower() or "integer" in stderr.lower()

    def test_unknown_option(self):
        """Unknown option exits 2."""
        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--unknown-flag"
            ],
            stdin_text="test\n"
        )

        assert code == 2
        assert "unknown" in stderr.lower()


class TestLexiconMapRedactionPreview:
    """Tests for redaction preview functionality."""

    def test_preview_respects_limit(self):
        """Preview respects --limit option."""
        if not GHANA_CORE_PACK.exists():
            import pytest
            pytest.skip("ghana-core pack not found")

        # Input with multiple terms
        input_text = (
            "Accra Kumasi Tamale Takoradi Cape Coast Tema "
            "Sunyani Ho Koforidua Bolgatanga Wa Techiman\n"
        )

        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--pack", str(GHANA_CORE_PACK),
                "--fixed-time", "2025-01-01T00:00:00Z",
                "--limit", "3"
            ],
            stdin_text=input_text
        )

        assert code == 0

        data = json.loads(stdout)
        assert len(data["redaction_preview"]) <= 3

    def test_preview_contains_context(self):
        """Preview entries contain context."""
        if not GHANA_CORE_PACK.exists():
            import pytest
            pytest.skip("ghana-core pack not found")

        input_text = "Visit Accra today.\n"

        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--pack", str(GHANA_CORE_PACK),
                "--fixed-time", "2025-01-01T00:00:00Z"
            ],
            stdin_text=input_text
        )

        assert code == 0

        data = json.loads(stdout)

        if data["redaction_preview"]:
            preview = data["redaction_preview"][0]
            assert "original" in preview
            assert "redacted" in preview
            assert "context" in preview


class TestLexiconMapCaseInsensitive:
    """Tests for case-insensitive matching."""

    def test_case_insensitive_matching(self):
        """Matching is case-insensitive (casefolded)."""
        if not GHANA_CORE_PACK.exists():
            import pytest
            pytest.skip("ghana-core pack not found")

        # Use lowercase and uppercase variants
        input_text = "Visit ACCRA and accra and Accra.\n"

        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--pack", str(GHANA_CORE_PACK),
                "--fixed-time", "2025-01-01T00:00:00Z"
            ],
            stdin_text=input_text
        )

        assert code == 0

        data = json.loads(stdout)

        # Should find Accra with count 3
        accra_match = next(
            (m for m in data["matches"] if m["term"] == "Accra"),
            None
        )
        assert accra_match is not None
        assert accra_match["count"] == 3


class TestLexiconMapWordBoundary:
    """Tests for word boundary matching."""

    def test_no_partial_word_match(self):
        """Does not match partial words."""
        if not GHANA_CORE_PACK.exists():
            import pytest
            pytest.skip("ghana-core pack not found")

        # "Wa" is a city in Ghana, but "walking" should not match
        input_text = "I am walking in Wa today.\n"

        stdout, stderr, code = run_cli(
            [
                "lexicon-map",
                "--pack", str(GHANA_CORE_PACK),
                "--fixed-time", "2025-01-01T00:00:00Z"
            ],
            stdin_text=input_text
        )

        assert code == 0

        data = json.loads(stdout)

        # Should only match "Wa" once
        wa_match = next(
            (m for m in data["matches"] if m["term"] == "Wa"),
            None
        )
        if wa_match:
            assert wa_match["count"] == 1
