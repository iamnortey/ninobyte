"""
CompliancePack Directory Scan Tests.

Tests for multi-file/directory scanning via CLI.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def run_cli(*args: str, cwd: Path = None) -> subprocess.CompletedProcess:
    """Run the CompliancePack CLI with given arguments."""
    cmd = [sys.executable, "-m", "compliancepack", *args]
    env = {"PYTHONPATH": str(Path(__file__).parent.parent / "src")}
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd or Path(__file__).parent.parent,
        env={**dict(os.environ), **env},
    )


def get_scan_tree_path() -> Path:
    """Get the scan_tree fixture path."""
    return Path(__file__).parent / "fixtures" / "scan_tree"


class TestDirectoryScan:
    """Tests for directory scanning."""

    def test_directory_scan_produces_findings(self):
        """Scanning a directory produces findings."""
        scan_tree = get_scan_tree_path()
        if not scan_tree.exists():
            pytest.skip("scan_tree fixture not found")

        result = run_cli(
            "check",
            "--input", str(scan_tree),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)
        assert output["format"] == "compliancepack.check.v1"
        assert "inputs" in output
        assert "scan_stats" in output
        assert output["scan_stats"]["files_scanned"] >= 1

    def test_directory_scan_has_file_in_samples(self):
        """Directory scan samples include file path."""
        scan_tree = get_scan_tree_path()
        if not scan_tree.exists():
            pytest.skip("scan_tree fixture not found")

        result = run_cli(
            "check",
            "--input", str(scan_tree),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)

        for finding in output["findings"]:
            for sample in finding["samples"]:
                assert "file" in sample
                assert sample["file"]  # Not empty

    def test_directory_scan_deterministic(self):
        """Directory scan is deterministic."""
        scan_tree = get_scan_tree_path()
        if not scan_tree.exists():
            pytest.skip("scan_tree fixture not found")

        outputs = []
        for _ in range(3):
            result = run_cli(
                "check",
                "--input", str(scan_tree),
                "--pack", "secrets.v1",
                "--fixed-time", "2025-01-01T00:00:00Z",
            )
            assert result.returncode in (0, 3)
            outputs.append(result.stdout)

        # All outputs should be identical
        assert len(set(outputs)) == 1

    def test_extension_filter(self):
        """Extension filter limits scanned files."""
        scan_tree = get_scan_tree_path()
        if not scan_tree.exists():
            pytest.skip("scan_tree fixture not found")

        result = run_cli(
            "check",
            "--input", str(scan_tree),
            "--pack", "secrets.v1",
            "--include-ext", ".env",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)

        # Should only scan .env files
        assert output["scan_stats"]["files_scanned"] == 1

    def test_max_files_limit(self):
        """Max files limit caps scanning."""
        scan_tree = get_scan_tree_path()
        if not scan_tree.exists():
            pytest.skip("scan_tree fixture not found")

        result = run_cli(
            "check",
            "--input", str(scan_tree),
            "--pack", "secrets.v1",
            "--max-files", "2",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)

        # Should only scan max 2 files
        assert output["scan_stats"]["files_scanned"] <= 2


class TestMultipleInputs:
    """Tests for multiple input paths."""

    def test_multiple_input_flags(self, tmp_path: Path):
        """Multiple --input flags are supported."""
        dir1 = tmp_path / "dir1"
        dir1.mkdir()
        (dir1 / "file1.txt").write_text("AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE")

        dir2 = tmp_path / "dir2"
        dir2.mkdir()
        (dir2 / "file2.txt").write_text("password=secret123")

        result = run_cli(
            "check",
            "--input", str(dir1),
            "--input", str(dir2),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)

        # Should have both input roots
        assert len(output["inputs"]) == 2
        # Should scan files from both directories
        assert output["scan_stats"]["files_scanned"] == 2


class TestSingleFileBackwardCompatibility:
    """Tests for single-file input backward compatibility."""

    def test_single_file_has_input_path(self):
        """Single file input uses input_path field."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)

        # Single file uses input_path, not inputs
        assert "input_path" in output
        assert "inputs" not in output

    def test_single_file_no_scan_stats(self):
        """Single file input doesn't have scan_stats."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)

        # Single file mode doesn't have scan_stats
        assert "scan_stats" not in output


class TestExitCodes:
    """Tests for exit codes with directory scanning."""

    def test_no_findings_exit_zero(self, tmp_path: Path):
        """No findings returns exit 0."""
        (tmp_path / "clean.txt").write_text("just regular text")

        result = run_cli(
            "check",
            "--input", str(tmp_path),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode == 0

    def test_findings_above_threshold_exit_three(self):
        """Findings above threshold return exit 3."""
        scan_tree = get_scan_tree_path()
        if not scan_tree.exists():
            pytest.skip("scan_tree fixture not found")

        result = run_cli(
            "check",
            "--input", str(scan_tree),
            "--pack", "secrets.v1",
            "--fail-on", "medium",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        # Should have findings at/above medium
        assert result.returncode == 3

    def test_exit_zero_flag_overrides(self):
        """--exit-zero forces exit 0."""
        scan_tree = get_scan_tree_path()
        if not scan_tree.exists():
            pytest.skip("scan_tree fixture not found")

        result = run_cli(
            "check",
            "--input", str(scan_tree),
            "--pack", "secrets.v1",
            "--exit-zero",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode == 0


class TestOutputFormats:
    """Tests for output formats with directory scanning."""

    def test_sariflite_format(self):
        """SARIF-lite format works with directory scanning."""
        scan_tree = get_scan_tree_path()
        if not scan_tree.exists():
            pytest.skip("scan_tree fixture not found")

        result = run_cli(
            "check",
            "--input", str(scan_tree),
            "--pack", "secrets.v1",
            "--format", "compliancepack.sariflite.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)
        assert output["format"] == "compliancepack.sariflite.v1"


class TestFindingsOrdering:
    """Tests for deterministic findings ordering."""

    def test_findings_sorted_by_severity_then_id(self):
        """Findings are sorted by severity then id."""
        scan_tree = get_scan_tree_path()
        if not scan_tree.exists():
            pytest.skip("scan_tree fixture not found")

        result = run_cli(
            "check",
            "--input", str(scan_tree),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)

        findings = output["findings"]
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

        for i in range(len(findings) - 1):
            curr_sev = severity_order[findings[i]["severity"]]
            next_sev = severity_order[findings[i + 1]["severity"]]

            if curr_sev == next_sev:
                # Same severity - sort by id
                assert findings[i]["id"] <= findings[i + 1]["id"]
            else:
                # Different severity - more severe first
                assert curr_sev <= next_sev

    def test_samples_sorted_by_file_then_line(self):
        """Samples are sorted by file then line."""
        scan_tree = get_scan_tree_path()
        if not scan_tree.exists():
            pytest.skip("scan_tree fixture not found")

        result = run_cli(
            "check",
            "--input", str(scan_tree),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)

        for finding in output["findings"]:
            samples = finding["samples"]
            for i in range(len(samples) - 1):
                curr = samples[i]
                next_s = samples[i + 1]

                if curr["file"] == next_s["file"]:
                    if curr["line"] == next_s["line"]:
                        assert curr["col_start"] <= next_s["col_start"]
                    else:
                        assert curr["line"] < next_s["line"]
                else:
                    assert curr["file"] <= next_s["file"]
