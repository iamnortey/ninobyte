"""
CLI smoke tests for NetOpsPack.

Verifies that CLI help and basic commands work.
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestCLIHelp:
    """Tests for CLI help output."""

    def test_main_help(self):
        """Main help shows available commands."""
        result = subprocess.run(
            [sys.executable, "-m", "netopspack", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": str(Path(__file__).parent.parent / "src"),
            },
        )
        assert result.returncode == 0
        assert "diagnose" in result.stdout
        assert "Network operations toolkit" in result.stdout

    def test_version(self):
        """Version flag shows version."""
        result = subprocess.run(
            [sys.executable, "-m", "netopspack", "--version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": str(Path(__file__).parent.parent / "src"),
            },
        )
        assert result.returncode == 0
        assert "0.9.0" in result.stdout

    def test_diagnose_help(self):
        """Diagnose help shows options."""
        result = subprocess.run(
            [sys.executable, "-m", "netopspack", "diagnose", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": str(Path(__file__).parent.parent / "src"),
            },
        )
        assert result.returncode == 0
        assert "--input" in result.stdout
        assert "--format" in result.stdout
        assert "--fixed-time" in result.stdout
        assert "--redact" in result.stdout
        assert "--no-redact" in result.stdout

    def test_no_command_returns_error(self):
        """No command prints help and returns error."""
        result = subprocess.run(
            [sys.executable, "-m", "netopspack"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": str(Path(__file__).parent.parent / "src"),
            },
        )
        assert result.returncode == 2


class TestDiagnoseStub:
    """Tests for diagnose command stub behavior."""

    def test_diagnose_missing_input_fails(self):
        """Diagnose without --input fails."""
        result = subprocess.run(
            [sys.executable, "-m", "netopspack", "diagnose"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": str(Path(__file__).parent.parent / "src"),
            },
        )
        assert result.returncode == 2
        assert "--input" in result.stderr

    def test_diagnose_stub_returns_not_implemented(self):
        """Diagnose stub returns not implemented message."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "netopspack",
                "diagnose",
                "--input",
                "/tmp/fake.log",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": str(Path(__file__).parent.parent / "src"),
            },
        )
        assert result.returncode == 2
        assert "not yet implemented" in result.stderr
