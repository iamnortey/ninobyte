"""
CLI smoke tests for NetOpsPack.

Verifies that CLI help and basic commands work.

Also includes contract tests per Prompt 4/20:
- CLI subprocess tests with PYTHONPATH=src invocation
- Exit code validation
- JSON output format validation
- Byte-for-byte determinism
"""

import json
import os
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


class TestCLIContract:
    """
    Contract tests per Prompt 4/20.

    Verifies that CLI works with canonical PYTHONPATH=src invocation
    and produces deterministic output.
    """

    def _run_cli(
        self,
        netopspack_dir: Path,
        args: list[str],
    ) -> subprocess.CompletedProcess:
        """Run CLI using canonical PYTHONPATH=src invocation."""
        cmd = [sys.executable, "-m", "netopspack"] + args
        env = {
            **dict(os.environ),
            "PYTHONPATH": str(netopspack_dir / "src"),
        }
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=netopspack_dir,
            env=env,
        )

    def test_contract_exit_code_zero(self, fixtures_dir: Path, netopspack_dir: Path):
        """CLI returns exit code 0 on success."""
        result = self._run_cli(
            netopspack_dir,
            [
                "diagnose",
                "--input",
                str(fixtures_dir / "sample_syslog.log"),
                "--format",
                "syslog",
                "--fixed-time",
                "2025-01-01T00:00:00Z",
            ],
        )
        assert result.returncode == 0

    def test_contract_output_is_valid_json(self, fixtures_dir: Path, netopspack_dir: Path):
        """CLI outputs valid JSON."""
        result = self._run_cli(
            netopspack_dir,
            [
                "diagnose",
                "--input",
                str(fixtures_dir / "sample_syslog.log"),
                "--format",
                "syslog",
                "--fixed-time",
                "2025-01-01T00:00:00Z",
            ],
        )
        assert result.returncode == 0
        # Must parse as valid JSON
        report = json.loads(result.stdout)
        assert isinstance(report, dict)

    def test_contract_generated_at_equals_fixed_time(
        self, fixtures_dir: Path, netopspack_dir: Path
    ):
        """generated_at_utc equals --fixed-time value."""
        fixed_time = "2025-01-01T00:00:00Z"
        result = self._run_cli(
            netopspack_dir,
            [
                "diagnose",
                "--input",
                str(fixtures_dir / "sample_syslog.log"),
                "--format",
                "syslog",
                "--fixed-time",
                fixed_time,
            ],
        )
        assert result.returncode == 0
        report = json.loads(result.stdout)
        assert report["generated_at_utc"] == fixed_time

    def test_contract_invalid_format_exit_code_2(self, fixtures_dir: Path, netopspack_dir: Path):
        """Invalid --format value returns exit code 2."""
        result = self._run_cli(
            netopspack_dir,
            [
                "diagnose",
                "--input",
                str(fixtures_dir / "sample_syslog.log"),
                "--format",
                "invalid_format",
            ],
        )
        assert result.returncode == 2
        assert "invalid choice" in result.stderr.lower() or "invalid_format" in result.stderr.lower()

    def test_contract_json_newline_terminated(self, fixtures_dir: Path, netopspack_dir: Path):
        """JSON output is newline-terminated for POSIX compliance."""
        result = self._run_cli(
            netopspack_dir,
            [
                "diagnose",
                "--input",
                str(fixtures_dir / "sample_syslog.log"),
                "--format",
                "syslog",
                "--fixed-time",
                "2025-01-01T00:00:00Z",
            ],
        )
        assert result.returncode == 0
        assert result.stdout.endswith("\n")

    def test_contract_byte_for_byte_determinism(
        self, fixtures_dir: Path, netopspack_dir: Path
    ):
        """Two identical CLI runs produce byte-for-byte identical output."""
        args = [
            "diagnose",
            "--input",
            str(fixtures_dir / "sample_syslog.log"),
            "--format",
            "syslog",
            "--fixed-time",
            "2025-01-01T00:00:00Z",
            "--limit",
            "10",
        ]

        result1 = self._run_cli(netopspack_dir, args)
        result2 = self._run_cli(netopspack_dir, args)

        assert result1.returncode == 0
        assert result2.returncode == 0
        assert result1.stdout == result2.stdout

    def test_contract_all_formats_deterministic(
        self, fixtures_dir: Path, netopspack_dir: Path
    ):
        """All supported formats produce deterministic output."""
        formats_fixtures = [
            ("syslog", "sample_syslog.log"),
            ("nginx", "sample_nginx.log"),
            ("haproxy", "sample_haproxy.log"),
        ]

        for format_name, fixture_file in formats_fixtures:
            args = [
                "diagnose",
                "--input",
                str(fixtures_dir / fixture_file),
                "--format",
                format_name,
                "--fixed-time",
                "2025-01-01T00:00:00Z",
            ]

            result1 = self._run_cli(netopspack_dir, args)
            result2 = self._run_cli(netopspack_dir, args)

            assert result1.returncode == 0, f"{format_name} failed"
            assert result2.returncode == 0, f"{format_name} failed"
            assert result1.stdout == result2.stdout, f"{format_name} not deterministic"

    def test_contract_json_sorted_keys(self, fixtures_dir: Path, netopspack_dir: Path):
        """JSON output has sorted keys."""
        result = self._run_cli(
            netopspack_dir,
            [
                "diagnose",
                "--input",
                str(fixtures_dir / "sample_syslog.log"),
                "--format",
                "syslog",
                "--fixed-time",
                "2025-01-01T00:00:00Z",
            ],
        )
        assert result.returncode == 0

        # Parse and re-dump with sorted keys, should match
        report = json.loads(result.stdout)
        reserialized = json.dumps(report, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"
        assert result.stdout == reserialized
