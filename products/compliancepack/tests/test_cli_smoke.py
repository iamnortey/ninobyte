"""
CompliancePack CLI smoke tests.

Validates the CLI contract:
- Help text works
- Version output works
- check subcommand accepts required arguments
- Output is valid JSON with expected schema
"""

import json
import subprocess
import sys
import tempfile
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
        env={**dict(__import__("os").environ), **env},
    )


class TestCLIHelp:
    """Test CLI help output."""

    def test_main_help(self):
        """Main --help should succeed."""
        result = run_cli("--help")
        assert result.returncode == 0
        assert "compliancepack" in result.stdout.lower()

    def test_check_help(self):
        """check --help should succeed."""
        result = run_cli("check", "--help")
        assert result.returncode == 0
        assert "--input" in result.stdout
        assert "--fixed-time" in result.stdout
        assert "--redact" in result.stdout

    def test_version(self):
        """--version should output version string."""
        result = run_cli("--version")
        assert result.returncode == 0
        assert "0.10.0" in result.stdout


class TestCheckCommand:
    """Test the check subcommand."""

    def test_check_requires_input(self):
        """check requires --input argument."""
        result = run_cli("check")
        assert result.returncode != 0
        assert "required" in result.stderr.lower() or "input" in result.stderr.lower()

    def test_check_missing_file(self):
        """check with non-existent file should fail."""
        result = run_cli("check", "--input", "/nonexistent/path/file.json")
        assert result.returncode == 1
        assert "not found" in result.stderr.lower()

    def test_check_valid_file(self):
        """check with valid file should produce JSON output."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write('{"key": "value"}')
            temp_path = f.name

        try:
            result = run_cli(
                "check",
                "--input", temp_path,
                "--fixed-time", "2025-01-01T00:00:00Z",
            )
            assert result.returncode == 0

            # Output should be valid JSON
            output = json.loads(result.stdout)
            assert output["format"] == "compliance-check"
            assert output["version"] == "1.0.0"
            assert output["generated_at_utc"] == "2025-01-01T00:00:00Z"
            assert output["input_file"] == temp_path
            assert "violations" in output
            assert "summary" in output
        finally:
            Path(temp_path).unlink()

    def test_check_deterministic_output(self):
        """Same input + fixed-time should produce identical output."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write('{"test": "data"}')
            temp_path = f.name

        try:
            result1 = run_cli(
                "check",
                "--input", temp_path,
                "--fixed-time", "2025-01-01T00:00:00Z",
            )
            result2 = run_cli(
                "check",
                "--input", temp_path,
                "--fixed-time", "2025-01-01T00:00:00Z",
            )

            assert result1.returncode == 0
            assert result2.returncode == 0
            assert result1.stdout == result2.stdout
        finally:
            Path(temp_path).unlink()

    def test_check_redact_default_on(self):
        """Redaction should be ON by default."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write('{"secret": "password123"}')
            temp_path = f.name

        try:
            result = run_cli(
                "check",
                "--input", temp_path,
                "--fixed-time", "2025-01-01T00:00:00Z",
            )
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert output["redacted"] is True
        finally:
            Path(temp_path).unlink()

    def test_check_no_redact_flag(self):
        """--no-redact should disable redaction."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write('{"secret": "password123"}')
            temp_path = f.name

        try:
            result = run_cli(
                "check",
                "--input", temp_path,
                "--fixed-time", "2025-01-01T00:00:00Z",
                "--no-redact",
            )
            assert result.returncode == 0
            output = json.loads(result.stdout)
            assert output["redacted"] is False
        finally:
            Path(temp_path).unlink()
