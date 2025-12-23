"""
Tests for pack discovery and fleet verification.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from lexicon_packs.discover import (
    discover_packs,
    discover_packs_with_info,
    format_discovery_json,
    verify_all_packs,
    validate_discovery_root,
    PackInfo,
    VerifyResult,
    DiscoveryError,
)
from lexicon_packs.lockfile import write_lockfile


class TestValidateDiscoveryRoot:
    """Tests for discovery root validation."""

    def test_valid_directory(self, fixtures_dir: Path):
        """Valid directory passes validation."""
        # Should not raise
        validate_discovery_root(fixtures_dir)

    def test_nonexistent_directory(self):
        """Nonexistent directory raises error."""
        with pytest.raises(DiscoveryError, match="does not exist"):
            validate_discovery_root(Path("/nonexistent/path"))

    def test_file_not_directory(self, fixtures_dir: Path):
        """File instead of directory raises error."""
        file_path = fixtures_dir / "minimal_pack" / "pack.json"
        with pytest.raises(DiscoveryError, match="not a directory"):
            validate_discovery_root(file_path)


class TestDiscoverPacks:
    """Tests for pack discovery."""

    def test_discovers_single_pack(self, fixtures_dir: Path):
        """Discovers a single pack."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a single pack
            root = Path(tmpdir).resolve()  # Resolve symlinks (macOS /var -> /private/var)
            pack_dir = root / "test-pack"
            shutil.copytree(fixtures_dir / "minimal_pack", pack_dir)

            packs = discover_packs(root)

            assert len(packs) == 1
            assert packs[0] == pack_dir

    def test_discovers_multiple_packs(self, fixtures_dir: Path):
        """Discovers multiple packs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two packs
            pack1 = Path(tmpdir) / "alpha-pack"
            pack2 = Path(tmpdir) / "beta-pack"
            shutil.copytree(fixtures_dir / "minimal_pack", pack1)
            shutil.copytree(fixtures_dir / "minimal_pack", pack2)

            packs = discover_packs(Path(tmpdir))

            assert len(packs) == 2

    def test_discovery_is_sorted_deterministically(self, fixtures_dir: Path):
        """Discovered packs are sorted alphabetically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create packs in non-alphabetical order
            for name in ["zebra", "alpha", "middle"]:
                pack_dir = Path(tmpdir) / name
                shutil.copytree(fixtures_dir / "minimal_pack", pack_dir)

            packs = discover_packs(Path(tmpdir))

            assert len(packs) == 3
            assert packs[0].name == "alpha"
            assert packs[1].name == "middle"
            assert packs[2].name == "zebra"

    def test_discovers_nested_packs(self, fixtures_dir: Path):
        """Discovers packs in nested directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            nested = Path(tmpdir) / "level1" / "level2" / "nested-pack"
            shutil.copytree(fixtures_dir / "minimal_pack", nested)

            packs = discover_packs(Path(tmpdir))

            assert len(packs) == 1
            assert "nested-pack" in str(packs[0])

    def test_empty_directory_returns_empty_list(self):
        """Empty directory returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            packs = discover_packs(Path(tmpdir))

            assert packs == []

    def test_discovery_determinism(self, fixtures_dir: Path):
        """Discovery produces same results on repeated calls."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ["pack-a", "pack-b", "pack-c"]:
                pack_dir = Path(tmpdir) / name
                shutil.copytree(fixtures_dir / "minimal_pack", pack_dir)

            packs1 = discover_packs(Path(tmpdir))
            packs2 = discover_packs(Path(tmpdir))

            assert packs1 == packs2


class TestDiscoverPacksWithInfo:
    """Tests for pack discovery with metadata."""

    def test_includes_pack_metadata(self, minimal_pack_path: Path):
        """Discovered packs include metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pack_dir = Path(tmpdir) / "test-pack"
            shutil.copytree(minimal_pack_path, pack_dir)

            packs = discover_packs_with_info(Path(tmpdir))

            assert len(packs) == 1
            assert packs[0].pack_id == "minimal-test"
            assert packs[0].entry_count == 3
            assert packs[0].has_lockfile is False

    def test_detects_lockfile_presence(self, minimal_pack_path: Path):
        """Correctly detects lockfile presence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pack_dir = Path(tmpdir) / "test-pack"
            shutil.copytree(minimal_pack_path, pack_dir)

            # Before lockfile
            packs = discover_packs_with_info(Path(tmpdir))
            assert packs[0].has_lockfile is False

            # Create lockfile
            write_lockfile(pack_dir, fixed_time="2025-01-01T00:00:00Z")

            # After lockfile
            packs = discover_packs_with_info(Path(tmpdir))
            assert packs[0].has_lockfile is True

    def test_handles_invalid_pack_gracefully(self, fixtures_dir: Path):
        """Invalid packs are reported with errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pack_dir = Path(tmpdir) / "invalid-pack"
            shutil.copytree(fixtures_dir / "invalid_schema", pack_dir)

            packs = discover_packs_with_info(Path(tmpdir))

            assert len(packs) == 1
            assert packs[0].error is not None

    def test_relative_path_option(self, minimal_pack_path: Path):
        """Paths can be made relative to a base."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pack_dir = Path(tmpdir) / "subdir" / "test-pack"
            pack_dir.parent.mkdir(parents=True)
            shutil.copytree(minimal_pack_path, pack_dir)

            packs = discover_packs_with_info(
                Path(tmpdir) / "subdir",
                relative_to=Path(tmpdir)
            )

            assert str(packs[0].path).startswith("subdir")


class TestPackInfoToDict:
    """Tests for PackInfo serialization."""

    def test_basic_fields(self):
        """Basic fields are included."""
        info = PackInfo(
            pack_id="test",
            path=Path("test-pack"),
            has_lockfile=True,
            entry_count=10,
            entries_sha256="abc123",
        )

        d = info.to_dict()

        assert d["pack_id"] == "test"
        assert d["path"] == "test-pack"
        assert d["has_lockfile"] is True
        assert d["entry_count"] == 10
        assert d["entries_sha256"] == "abc123"

    def test_optional_fields_excluded_when_none(self):
        """None fields are excluded from output."""
        info = PackInfo(
            pack_id="test",
            path=Path("test-pack"),
            has_lockfile=False,
        )

        d = info.to_dict()

        assert "entry_count" not in d
        assert "entries_sha256" not in d
        assert "error" not in d

    def test_error_field_included_when_present(self):
        """Error field is included when present."""
        info = PackInfo(
            pack_id="test",
            path=Path("test-pack"),
            has_lockfile=False,
            error="Something went wrong",
        )

        d = info.to_dict()

        assert d["error"] == "Something went wrong"


class TestFormatDiscoveryJson:
    """Tests for discovery JSON formatting."""

    def test_includes_timestamp(self):
        """Output includes generated_at_utc."""
        packs = []
        output = format_discovery_json(packs)
        data = json.loads(output)

        assert "generated_at_utc" in data

    def test_fixed_time_honored(self):
        """Fixed time is used when provided."""
        packs = []
        fixed_time = "2025-06-15T12:00:00Z"
        output = format_discovery_json(packs, fixed_time=fixed_time)
        data = json.loads(output)

        assert data["generated_at_utc"] == fixed_time

    def test_pack_count_included(self):
        """Pack count is included."""
        packs = [
            PackInfo(pack_id="a", path=Path("a"), has_lockfile=True),
            PackInfo(pack_id="b", path=Path("b"), has_lockfile=True),
        ]
        output = format_discovery_json(packs)
        data = json.loads(output)

        assert data["pack_count"] == 2

    def test_output_is_canonical_json(self):
        """Output is canonical JSON."""
        packs = [
            PackInfo(pack_id="test", path=Path("test"), has_lockfile=True),
        ]
        output = format_discovery_json(packs, fixed_time="2025-01-01T00:00:00Z")

        # Should have trailing newline
        assert output.endswith("\n")

        # Keys should be sorted
        data = json.loads(output)
        keys = list(data.keys())
        assert keys == sorted(keys)


class TestVerifyAllPacks:
    """Tests for fleet verification."""

    def test_verifies_valid_fleet(self, minimal_pack_path: Path):
        """All valid packs pass verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two packs with lockfiles
            for name in ["pack-a", "pack-b"]:
                pack_dir = Path(tmpdir) / name
                shutil.copytree(minimal_pack_path, pack_dir)
                write_lockfile(pack_dir, fixed_time="2025-01-01T00:00:00Z")

            all_valid, results = verify_all_packs(Path(tmpdir))

            assert all_valid is True
            assert len(results) == 2
            assert all(r.valid for r in results)

    def test_fails_on_missing_lockfile(self, minimal_pack_path: Path):
        """Missing lockfile fails verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pack_dir = Path(tmpdir) / "test-pack"
            shutil.copytree(minimal_pack_path, pack_dir)
            # No lockfile created

            all_valid, results = verify_all_packs(Path(tmpdir))

            assert all_valid is False
            assert results[0].valid is False
            assert "Lockfile not found" in results[0].errors[0]

    def test_fails_on_drifted_lockfile(self, minimal_pack_path: Path):
        """Drifted lockfile fails verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pack_dir = Path(tmpdir) / "test-pack"
            shutil.copytree(minimal_pack_path, pack_dir)
            write_lockfile(pack_dir, fixed_time="2025-01-01T00:00:00Z")

            # Modify entries
            entries_path = pack_dir / "entries.csv"
            entries_path.write_text("term,category\nmodified,test\n")

            all_valid, results = verify_all_packs(Path(tmpdir))

            assert all_valid is False
            assert results[0].valid is False

    def test_fail_fast_stops_at_first_failure(self, minimal_pack_path: Path):
        """Fail-fast mode stops at first failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two packs without lockfiles
            for name in ["alpha", "beta"]:
                pack_dir = Path(tmpdir) / name
                shutil.copytree(minimal_pack_path, pack_dir)

            all_valid, results = verify_all_packs(Path(tmpdir), fail_fast=True)

            assert all_valid is False
            assert len(results) == 1  # Only first pack checked

    def test_no_fail_fast_checks_all(self, minimal_pack_path: Path):
        """Without fail-fast, all packs are checked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two packs without lockfiles
            for name in ["alpha", "beta"]:
                pack_dir = Path(tmpdir) / name
                shutil.copytree(minimal_pack_path, pack_dir)

            all_valid, results = verify_all_packs(Path(tmpdir), fail_fast=False)

            assert all_valid is False
            assert len(results) == 2  # Both checked


class TestVerifyResultToDict:
    """Tests for VerifyResult serialization."""

    def test_includes_all_fields(self):
        """All fields are included."""
        result = VerifyResult(
            pack_id="test",
            path=Path("test-pack"),
            valid=False,
            errors=["Error 1", "Error 2"],
        )

        d = result.to_dict()

        assert d["pack_id"] == "test"
        assert d["path"] == "test-pack"
        assert d["valid"] is False
        assert d["errors"] == ["Error 1", "Error 2"]


class TestCLIDiscover:
    """Tests for discover CLI command."""

    def test_discover_outputs_json(self, minimal_pack_path: Path):
        """discover command outputs valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pack_dir = Path(tmpdir) / "test-pack"
            shutil.copytree(minimal_pack_path, pack_dir)

            src_dir = minimal_pack_path.parent.parent.parent / "src"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lexicon_packs",
                    "discover",
                    "--root",
                    str(tmpdir),
                    "--fixed-time",
                    "2025-01-01T00:00:00Z",
                ],
                capture_output=True,
                text=True,
                cwd=str(src_dir.parent),
                env={
                    **subprocess.os.environ,
                    "PYTHONPATH": str(src_dir),
                },
            )

            assert result.returncode == 0
            data = json.loads(result.stdout)
            assert data["pack_count"] == 1

    def test_discover_deterministic_output(self, minimal_pack_path: Path):
        """discover produces deterministic output with fixed-time."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pack_dir = Path(tmpdir) / "test-pack"
            shutil.copytree(minimal_pack_path, pack_dir)

            src_dir = minimal_pack_path.parent.parent.parent / "src"

            def run_discover():
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "lexicon_packs",
                        "discover",
                        "--root",
                        str(tmpdir),
                        "--fixed-time",
                        "2025-01-01T00:00:00Z",
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

            output1 = run_discover()
            output2 = run_discover()

            assert output1 == output2


class TestCLIVerifyAll:
    """Tests for verify-all CLI command."""

    def test_verify_all_success(self, minimal_pack_path: Path):
        """verify-all succeeds with valid lockfiles."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pack_dir = Path(tmpdir) / "test-pack"
            shutil.copytree(minimal_pack_path, pack_dir)
            write_lockfile(pack_dir, fixed_time="2025-01-01T00:00:00Z")

            src_dir = minimal_pack_path.parent.parent.parent / "src"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lexicon_packs",
                    "verify-all",
                    "--root",
                    str(tmpdir),
                ],
                capture_output=True,
                text=True,
                cwd=str(src_dir.parent),
                env={
                    **subprocess.os.environ,
                    "PYTHONPATH": str(src_dir),
                },
            )

            assert result.returncode == 0
            assert "Verified 1 pack" in result.stdout

    def test_verify_all_failure(self, minimal_pack_path: Path):
        """verify-all fails with missing lockfile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pack_dir = Path(tmpdir) / "test-pack"
            shutil.copytree(minimal_pack_path, pack_dir)
            # No lockfile

            src_dir = minimal_pack_path.parent.parent.parent / "src"

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "lexicon_packs",
                    "verify-all",
                    "--root",
                    str(tmpdir),
                ],
                capture_output=True,
                text=True,
                cwd=str(src_dir.parent),
                env={
                    **subprocess.os.environ,
                    "PYTHONPATH": str(src_dir),
                },
            )

            assert result.returncode == 2
            assert "FAILED" in result.stderr

    def test_verify_all_missing_root(self, minimal_pack_path: Path):
        """verify-all fails with nonexistent root."""
        src_dir = minimal_pack_path.parent.parent.parent / "src"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "lexicon_packs",
                "verify-all",
                "--root",
                "/nonexistent/path",
            ],
            capture_output=True,
            text=True,
            cwd=str(src_dir.parent),
            env={
                **subprocess.os.environ,
                "PYTHONPATH": str(src_dir),
            },
        )

        assert result.returncode == 2
        assert "not found" in result.stderr


class TestRealPacksIntegration:
    """Integration tests with real packs."""

    def test_discovers_real_packs(self, ghana_core_path: Path):
        """Discovers real packs in repository."""
        packs_root = ghana_core_path.parent

        packs = discover_packs(packs_root)

        # Should find at least ghana-core
        pack_ids = [p.name for p in packs]
        assert "ghana-core" in pack_ids

    def test_verify_all_real_packs(self, ghana_core_path: Path):
        """Verifies all real packs in repository."""
        packs_root = ghana_core_path.parent

        all_valid, results = verify_all_packs(packs_root)

        # All real packs should have valid lockfiles
        assert all_valid is True
        assert len(results) >= 1
