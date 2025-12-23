"""
CLI smoke tests for NetOpsPack.

Verifies that CLI help and basic commands work.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def netopspack_dir() -> Path:
    """Path to netopspack package."""
    return Path(__file__).parent.parent


class TestCLIHelp:
    """Tests for CLI help output."""

    def test_main_help(self, netopspack_dir: Path):
        """Main help shows available commands."""
        result = subprocess.run(
            [sys.executable, "-m", "netopspack", "--help"],
            capture_output=True,
            text=True,
            cwd=netopspack_dir,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": str(netopspack_dir / "src"),
            },
        )
        assert result.returncode == 0
        assert "diagnose" in result.stdout
        assert "Network operations toolkit" in result.stdout

    def test_version(self, netopspack_dir: Path):
        """Version flag shows version."""
        result = subprocess.run(
            [sys.executable, "-m", "netopspack", "--version"],
            capture_output=True,
            text=True,
            cwd=netopspack_dir,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": str(netopspack_dir / "src"),
            },
        )
        assert result.returncode == 0
        assert "0.9.0" in result.stdout

    def test_diagnose_help(self, netopspack_dir: Path):
        """Diagnose help shows options."""
        result = subprocess.run(
            [sys.executable, "-m", "netopspack", "diagnose", "--help"],
            capture_output=True,
            text=True,
            cwd=netopspack_dir,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": str(netopspack_dir / "src"),
            },
        )
        assert result.returncode == 0
        assert "--input" in result.stdout
        assert "--format" in result.stdout
        assert "--fixed-time" in result.stdout
        assert "--redact" in result.stdout
        assert "--no-redact" in result.stdout
        assert "--limit" in result.stdout

    def test_no_command_returns_error(self, netopspack_dir: Path):
        """No command prints help and returns error."""
        result = subprocess.run(
            [sys.executable, "-m", "netopspack"],
            capture_output=True,
            text=True,
            cwd=netopspack_dir,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": str(netopspack_dir / "src"),
            },
        )
        assert result.returncode == 2


class TestDiagnoseCommand:
    """Tests for diagnose command behavior."""

    def test_diagnose_missing_input_fails(self, netopspack_dir: Path):
        """Diagnose without --input fails."""
        result = subprocess.run(
            [sys.executable, "-m", "netopspack", "diagnose"],
            capture_output=True,
            text=True,
            cwd=netopspack_dir,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": str(netopspack_dir / "src"),
            },
        )
        assert result.returncode == 2
        assert "--input" in result.stderr

    def test_diagnose_nonexistent_file_fails(self, netopspack_dir: Path):
        """Diagnose with nonexistent file fails."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "netopspack",
                "diagnose",
                "--input",
                "/nonexistent/file.log",
            ],
            capture_output=True,
            text=True,
            cwd=netopspack_dir,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": str(netopspack_dir / "src"),
            },
        )
        assert result.returncode == 2
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_diagnose_valid_file_succeeds(self, fixtures_dir: Path, netopspack_dir: Path):
        """Diagnose with valid file succeeds."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "netopspack",
                "diagnose",
                "--input",
                str(fixtures_dir / "sample_syslog.log"),
                "--fixed-time",
                "2025-01-01T00:00:00Z",
            ],
            capture_output=True,
            text=True,
            cwd=netopspack_dir,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": str(netopspack_dir / "src"),
            },
        )
        assert result.returncode == 0
        # Output should be valid JSON
        report = json.loads(result.stdout)
        assert "schema_version" in report
        assert "events" in report

    def test_diagnose_outputs_json(self, fixtures_dir: Path, netopspack_dir: Path):
        """Diagnose outputs valid JSON."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "netopspack",
                "diagnose",
                "--input",
                str(fixtures_dir / "sample_nginx.log"),
                "--format",
                "nginx",
                "--fixed-time",
                "2025-01-01T00:00:00Z",
            ],
            capture_output=True,
            text=True,
            cwd=netopspack_dir,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": str(netopspack_dir / "src"),
            },
        )
        assert result.returncode == 0
        report = json.loads(result.stdout)
        assert report["format"] == "nginx"
        assert report["event_count"] > 0
