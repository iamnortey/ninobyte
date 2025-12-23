"""
CLI smoke tests for OpsPack.

Verifies basic CLI functionality works as expected.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

OPSPACK_DIR = Path(__file__).parent.parent


def test_help_returns_zero():
    """CLI --help should return exit code 0."""
    result = subprocess.run(
        [sys.executable, "-m", "opspack", "--help"],
        capture_output=True,
        text=True,
        cwd=OPSPACK_DIR / "src",
    )
    assert result.returncode == 0
    assert "OpsPack" in result.stdout
    assert "triage" in result.stdout


def test_version_flag():
    """CLI --version should show version."""
    result = subprocess.run(
        [sys.executable, "-m", "opspack", "--version"],
        capture_output=True,
        text=True,
        cwd=OPSPACK_DIR / "src",
    )
    assert result.returncode == 0
    assert "0.1.0" in result.stdout


def test_triage_help():
    """CLI triage --help should show triage options."""
    result = subprocess.run(
        [sys.executable, "-m", "opspack", "triage", "--help"],
        capture_output=True,
        text=True,
        cwd=OPSPACK_DIR / "src",
    )
    assert result.returncode == 0
    assert "--input" in result.stdout
    assert "--output" in result.stdout


def test_triage_missing_input():
    """CLI triage without --input should fail."""
    result = subprocess.run(
        [sys.executable, "-m", "opspack", "triage"],
        capture_output=True,
        text=True,
        cwd=OPSPACK_DIR / "src",
    )
    assert result.returncode != 0
    assert "required" in result.stderr.lower()


def test_triage_nonexistent_file():
    """CLI triage with non-existent file should fail gracefully."""
    result = subprocess.run(
        [sys.executable, "-m", "opspack", "triage", "--input", "/nonexistent/path/file.log"],
        capture_output=True,
        text=True,
        cwd=OPSPACK_DIR / "src",
    )
    assert result.returncode == 1
    assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()


def test_triage_produces_valid_json(tmp_path):
    """CLI triage should produce valid JSON output."""
    # Create a test input file
    test_file = tmp_path / "test.log"
    test_file.write_text("2024-01-15T10:30:00Z ERROR Something failed\n")

    result = subprocess.run(
        [
            sys.executable, "-m", "opspack", "triage",
            "--input", str(test_file),
            "--fixed-time", "2024-01-01T00:00:00Z"
        ],
        capture_output=True,
        text=True,
        cwd=OPSPACK_DIR / "src",
    )
    assert result.returncode == 0

    # Should be valid JSON
    output = json.loads(result.stdout)
    assert "schema_version" in output
    assert "signals" in output
    assert "redaction_applied" in output
