"""
Tests for deterministic output.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from lexicon_packs.load import load_pack
from lexicon_packs.canonicalize import (
    canonicalize_json,
    canonicalize_json_compact,
    compute_sha256,
    compute_entries_hash,
)


class TestCanonicalJSON:
    """Tests for canonical JSON formatting."""

    def test_sorted_keys(self):
        """Output has sorted keys."""
        data = {"zebra": 1, "alpha": 2, "middle": 3}
        result = canonicalize_json(data)

        # Keys should appear in sorted order
        assert result.index('"alpha"') < result.index('"middle"')
        assert result.index('"middle"') < result.index('"zebra"')

    def test_nested_sorted_keys(self):
        """Nested objects have sorted keys."""
        data = {"outer": {"zebra": 1, "alpha": 2}}
        result = canonicalize_json(data)

        assert result.index('"alpha"') < result.index('"zebra"')

    def test_two_space_indent(self):
        """Output uses 2-space indent."""
        data = {"key": {"nested": "value"}}
        result = canonicalize_json(data)

        # Check for 2-space indent
        assert '  "key"' in result
        assert '    "nested"' in result

    def test_trailing_newline(self):
        """Output has trailing newline."""
        result = canonicalize_json({"key": "value"})

        assert result.endswith("\n")

    def test_compact_no_whitespace(self):
        """Compact format has no extra whitespace."""
        data = {"key": "value", "num": 42}
        result = canonicalize_json_compact(data)

        assert " " not in result
        assert "\n" not in result
        assert result == '{"key":"value","num":42}'


class TestDeterministicHash:
    """Tests for deterministic hashing."""

    def test_same_input_same_hash(self):
        """Same input produces same hash."""
        data = "test string"

        hash1 = compute_sha256(data)
        hash2 = compute_sha256(data)

        assert hash1 == hash2

    def test_entries_hash_stable(self):
        """Entries hash is stable across calls."""
        entries = [
            {"term": "alpha", "category": "letter"},
            {"term": "beta", "category": "letter"},
        ]

        hash1 = compute_entries_hash(entries)
        hash2 = compute_entries_hash(entries)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex

    def test_entries_hash_order_sensitive(self):
        """Entries hash changes with order."""
        entries1 = [
            {"term": "alpha", "category": "letter"},
            {"term": "beta", "category": "letter"},
        ]
        entries2 = [
            {"term": "beta", "category": "letter"},
            {"term": "alpha", "category": "letter"},
        ]

        hash1 = compute_entries_hash(entries1)
        hash2 = compute_entries_hash(entries2)

        assert hash1 != hash2


class TestLoadedPackDeterminism:
    """Tests for deterministic pack loading."""

    def test_entries_sha256_stable(self, minimal_pack_path: Path):
        """entries_sha256 is stable across loads."""
        pack1 = load_pack(minimal_pack_path)
        pack2 = load_pack(minimal_pack_path)

        assert pack1.entries_sha256 == pack2.entries_sha256

    def test_to_dict_stable(self, minimal_pack_path: Path):
        """to_dict output is stable."""
        pack1 = load_pack(minimal_pack_path)
        pack2 = load_pack(minimal_pack_path)

        json1 = canonicalize_json(pack1.to_dict(include_entries=3))
        json2 = canonicalize_json(pack2.to_dict(include_entries=3))

        assert json1 == json2

    def test_ghana_core_hash_stable(self, ghana_core_path: Path):
        """Ghana core entries hash is stable."""
        pack1 = load_pack(ghana_core_path)
        pack2 = load_pack(ghana_core_path)

        assert pack1.entries_sha256 == pack2.entries_sha256


class TestCLIDeterminism:
    """Tests for CLI output determinism."""

    def test_show_output_stable(self, ghana_core_path: Path):
        """CLI show output is byte-for-byte stable."""
        src_dir = ghana_core_path.parent.parent / "src"

        def run_show():
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lexicon_packs",
                    "show",
                    "--pack",
                    str(ghana_core_path),
                    "--output",
                    "json",
                    "--limit",
                    "5",
                ],
                capture_output=True,
                text=True,
                cwd=str(src_dir.parent),
                env={
                    **subprocess.os.environ,
                    "PYTHONPATH": str(src_dir),
                },
            )
            return result.stdout

        output1 = run_show()
        output2 = run_show()

        assert output1 == output2
        assert len(output1) > 0

    def test_validate_exit_codes(self, minimal_pack_path: Path, invalid_schema_path: Path):
        """Validate command has correct exit codes."""
        src_dir = minimal_pack_path.parent.parent.parent / "src"

        def run_validate(pack_path: Path) -> int:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lexicon_packs",
                    "validate",
                    "--pack",
                    str(pack_path),
                ],
                capture_output=True,
                cwd=str(src_dir.parent),
                env={
                    **subprocess.os.environ,
                    "PYTHONPATH": str(src_dir),
                },
            )
            return result.returncode

        # Valid pack -> exit 0
        assert run_validate(minimal_pack_path) == 0

        # Invalid pack -> exit 2
        assert run_validate(invalid_schema_path) == 2
