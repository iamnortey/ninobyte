"""
CompliancePack Scanner Tests.

Tests for directory traversal, file reading, and security boundaries.
"""

import os
import tempfile
from pathlib import Path
from typing import Set

import pytest

from compliancepack.scanner import (
    ScanError,
    collect_targets,
    read_file_limited,
    summarize_skipped,
)


class TestCollectTargets:
    """Tests for collect_targets function."""

    def test_collect_single_file(self, tmp_path: Path):
        """Single file input returns that file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        files, skipped = collect_targets([test_file])

        assert len(files) == 1
        assert files[0] == test_file.resolve()
        assert len(skipped) == 0

    def test_collect_directory(self, tmp_path: Path):
        """Directory input returns all files."""
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "c.txt").write_text("c")

        files, skipped = collect_targets([tmp_path])

        assert len(files) == 3
        # Files should be sorted
        names = [f.name for f in files]
        assert names == sorted(names)

    def test_deterministic_order(self, tmp_path: Path):
        """Files are returned in deterministic order."""
        # Create files in random order
        for name in ["z.txt", "a.txt", "m.txt", "b.txt"]:
            (tmp_path / name).write_text(name)

        files1, _ = collect_targets([tmp_path])
        files2, _ = collect_targets([tmp_path])

        assert files1 == files2
        # Should be sorted by path
        assert [f.name for f in files1] == ["a.txt", "b.txt", "m.txt", "z.txt"]

    def test_extension_filter(self, tmp_path: Path):
        """Extension filter limits files scanned."""
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.log").write_text("b")
        (tmp_path / "c.env").write_text("c")

        files, skipped = collect_targets(
            [tmp_path],
            include_extensions={".txt", ".env"},
        )

        assert len(files) == 2
        names = {f.name for f in files}
        assert names == {"a.txt", "c.env"}

    def test_extension_filter_case_insensitive(self, tmp_path: Path):
        """Extension filter is case-insensitive."""
        (tmp_path / "a.TXT").write_text("a")
        (tmp_path / "b.txt").write_text("b")

        files, skipped = collect_targets(
            [tmp_path],
            include_extensions={".txt"},
        )

        # Both should match
        assert len(files) == 2

    def test_max_files_limit(self, tmp_path: Path):
        """Max files limit caps collection."""
        for i in range(10):
            (tmp_path / f"file{i:02d}.txt").write_text(f"content{i}")

        files, skipped = collect_targets([tmp_path], max_files=5)

        assert len(files) == 5
        # Should have truncation notice in skipped
        assert any("max_files_exceeded" in reason for _, reason in skipped)

    def test_max_files_deterministic_truncation(self, tmp_path: Path):
        """Max files truncation is deterministic."""
        for i in range(10):
            (tmp_path / f"file{i:02d}.txt").write_text(f"content{i}")

        files1, _ = collect_targets([tmp_path], max_files=5)
        files2, _ = collect_targets([tmp_path], max_files=5)

        assert files1 == files2

    def test_symlink_default_skipped(self, tmp_path: Path):
        """Symlinks are skipped by default."""
        real_file = tmp_path / "real.txt"
        real_file.write_text("real")
        link = tmp_path / "link.txt"
        link.symlink_to(real_file)

        files, skipped = collect_targets([tmp_path], follow_symlinks=False)

        assert len(files) == 1
        assert files[0].name == "real.txt"
        assert any("symlink_skipped" in reason for _, reason in skipped)

    def test_symlink_followed_when_enabled(self, tmp_path: Path):
        """Symlinks are followed when enabled."""
        real_file = tmp_path / "real.txt"
        real_file.write_text("real")
        link = tmp_path / "link.txt"
        link.symlink_to(real_file)

        files, skipped = collect_targets([tmp_path], follow_symlinks=True)

        # Both the real file and symlink resolve to the same path
        # so we should get the file once (deduplicated by resolve())
        assert len(files) == 1

    def test_symlink_escape_blocked(self, tmp_path: Path):
        """Symlinks escaping boundary are blocked even when following."""
        # Create a file outside the scan boundary
        outside = tmp_path.parent / "outside.txt"
        outside.write_text("outside")

        scan_dir = tmp_path / "scan"
        scan_dir.mkdir()
        escape_link = scan_dir / "escape.txt"
        escape_link.symlink_to(outside)

        files, skipped = collect_targets([scan_dir], follow_symlinks=True)

        assert len(files) == 0
        # The escape is detected either as path_traversal or symlink_escape
        # depending on when the boundary check happens
        assert any(
            "symlink_escape" in reason or "path_traversal" in reason
            for _, reason in skipped
        )

        # Cleanup
        outside.unlink()

    def test_nonexistent_input_skipped(self, tmp_path: Path):
        """Nonexistent inputs are skipped."""
        nonexistent = tmp_path / "does_not_exist"

        files, skipped = collect_targets([nonexistent])

        assert len(files) == 0
        assert any("not_found" in reason for _, reason in skipped)

    def test_multiple_inputs(self, tmp_path: Path):
        """Multiple inputs are combined."""
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "a.txt").write_text("a")

        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        (dir2 / "b.txt").write_text("b")

        files, skipped = collect_targets([dir1, dir2])

        assert len(files) == 2

    def test_path_traversal_blocked(self, tmp_path: Path):
        """Path traversal attempts are blocked."""
        scan_dir = tmp_path / "scan"
        scan_dir.mkdir()
        (scan_dir / "safe.txt").write_text("safe")

        # Try to escape via symlink with ..
        parent_file = tmp_path / "parent.txt"
        parent_file.write_text("parent")

        escape_link = scan_dir / "escape"
        escape_link.symlink_to(Path("..") / "parent.txt")

        files, skipped = collect_targets([scan_dir], follow_symlinks=True)

        # Should only get safe.txt
        assert len(files) == 1
        assert files[0].name == "safe.txt"

    def test_max_files_validation(self, tmp_path: Path):
        """max_files must be >= 1."""
        with pytest.raises(ValueError, match="max_files must be >= 1"):
            collect_targets([tmp_path], max_files=0)


class TestReadFileLimited:
    """Tests for read_file_limited function."""

    def test_read_small_file(self, tmp_path: Path):
        """Small files are read completely."""
        test_file = tmp_path / "small.txt"
        content = "Hello, World!"
        test_file.write_text(content)

        result, truncated = read_file_limited(test_file)

        assert result == content
        assert not truncated

    def test_read_truncated_file(self, tmp_path: Path):
        """Large files are truncated."""
        test_file = tmp_path / "large.txt"
        content = "x" * 1000
        test_file.write_text(content)

        result, truncated = read_file_limited(test_file, max_bytes=100)

        assert len(result) == 100
        assert truncated

    def test_utf8_decode(self, tmp_path: Path):
        """UTF-8 content is decoded correctly."""
        test_file = tmp_path / "utf8.txt"
        content = "Hello, 世界! 🌍"
        test_file.write_text(content, encoding="utf-8")

        result, truncated = read_file_limited(test_file)

        assert result == content
        assert not truncated

    def test_latin1_fallback(self, tmp_path: Path):
        """Non-UTF8 content falls back to latin-1."""
        test_file = tmp_path / "latin1.txt"
        # Write raw bytes that aren't valid UTF-8
        test_file.write_bytes(b"\xff\xfe Hello")

        result, truncated = read_file_limited(test_file)

        # Should not raise, content decoded as latin-1
        assert "Hello" in result

    def test_file_not_found(self, tmp_path: Path):
        """Missing file raises ScanError."""
        missing = tmp_path / "missing.txt"

        with pytest.raises(ScanError, match="File not found"):
            read_file_limited(missing)

    def test_max_bytes_validation(self, tmp_path: Path):
        """max_bytes must be >= 1."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        with pytest.raises(ValueError, match="max_bytes must be >= 1"):
            read_file_limited(test_file, max_bytes=0)


class TestSummarizeSkipped:
    """Tests for summarize_skipped function."""

    def test_empty_list(self):
        """Empty list returns empty dict."""
        result = summarize_skipped([])
        assert result == {}

    def test_counts_reasons(self):
        """Reasons are counted correctly."""
        skipped = [
            (Path("a"), "not_found"),
            (Path("b"), "symlink_skipped"),
            (Path("c"), "not_found"),
            (Path("d"), "permission_denied"),
        ]

        result = summarize_skipped(skipped)

        assert result["not_found"] == 2
        assert result["symlink_skipped"] == 1
        assert result["permission_denied"] == 1

    def test_keys_sorted(self):
        """Keys are sorted for determinism."""
        skipped = [
            (Path("a"), "z_reason"),
            (Path("b"), "a_reason"),
            (Path("c"), "m_reason"),
        ]

        result = summarize_skipped(skipped)

        assert list(result.keys()) == ["a_reason", "m_reason", "z_reason"]

    def test_dynamic_reasons_normalized(self):
        """Dynamic reasons are normalized."""
        skipped = [
            (Path("a"), "resolve_error:OSError"),
            (Path("b"), "resolve_error:PermissionError"),
            (Path("c"), "read_error:IOError"),
        ]

        result = summarize_skipped(skipped)

        assert result["resolve_error"] == 2
        assert result["read_error"] == 1


class TestDirectoryScanIntegration:
    """Integration tests for directory scanning."""

    def test_scan_tree_fixture(self):
        """Scan the test fixture directory."""
        fixtures_dir = Path(__file__).parent / "fixtures" / "scan_tree"
        if not fixtures_dir.exists():
            pytest.skip("scan_tree fixture not found")

        files, skipped = collect_targets([fixtures_dir])

        # Should find all 4 files
        assert len(files) >= 4

    def test_scan_with_extension_filter(self):
        """Scan fixture with extension filter."""
        fixtures_dir = Path(__file__).parent / "fixtures" / "scan_tree"
        if not fixtures_dir.exists():
            pytest.skip("scan_tree fixture not found")

        files, skipped = collect_targets(
            [fixtures_dir],
            include_extensions={".env"},
        )

        # Should only find config.env
        assert len(files) == 1
        assert files[0].name == "config.env"
