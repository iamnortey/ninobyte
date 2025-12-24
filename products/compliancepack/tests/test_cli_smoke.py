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
        assert "--policy" in result.stdout
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
        fixtures = Path(__file__).parent / "fixtures"
        policy_file = fixtures / "policy_v1.json"

        result = run_cli("check", "--policy", str(policy_file))
        assert result.returncode != 0
        assert "required" in result.stderr.lower() or "input" in result.stderr.lower()

    def test_check_requires_policy(self):
        """check requires --policy argument."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli("check", "--input", str(input_file))
        assert result.returncode != 0
        assert "required" in result.stderr.lower() or "policy" in result.stderr.lower()

    def test_check_missing_input_file(self):
        """check with non-existent input file should fail."""
        fixtures = Path(__file__).parent / "fixtures"
        policy_file = fixtures / "policy_v1.json"

        result = run_cli(
            "check",
            "--input", "/nonexistent/path/file.json",
            "--policy", str(policy_file),
        )
        assert result.returncode == 1
        assert "not found" in result.stderr.lower()

    def test_check_missing_policy_file(self):
        """check with non-existent policy file should fail."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--policy", "/nonexistent/policy.json",
        )
        assert result.returncode == 1
        assert "not found" in result.stderr.lower()

    def test_check_with_fixtures(self):
        """check with valid fixtures should produce JSON output."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"
        policy_file = fixtures / "policy_v1.json"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--policy", str(policy_file),
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode == 0

        # Output should be valid JSON
        output = json.loads(result.stdout)
        assert output["format"] == "compliancepack.check.v1"
        assert output["generated_at_utc"] == "2025-01-01T00:00:00Z"
        assert "findings" in output
        assert "summary" in output

    def test_check_finds_expected_violations(self):
        """check should find expected violations in sample input."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"
        policy_file = fixtures / "policy_v1.json"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--policy", str(policy_file),
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)

        # Should find 3 findings: AWS key, email, private key
        assert output["summary"]["finding_count"] == 3
        assert output["summary"]["policy_count"] == 3

        # Check severity counts
        counts = output["summary"]["severity_counts"]
        assert counts["critical"] == 1  # Private key
        assert counts["high"] == 1  # AWS key
        assert counts["medium"] == 1  # Email

    def test_check_output_format(self):
        """Output should have correct format field."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"
        policy_file = fixtures / "policy_v1.json"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--policy", str(policy_file),
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["format"] == "compliancepack.check.v1"


class TestRedactionFlag:
    """Test --redact and --no-redact flags."""

    def test_redact_default_on(self):
        """Redaction should be ON by default."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"
        policy_file = fixtures / "policy_v1.json"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--policy", str(policy_file),
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["redaction_applied"] is True

        # Sensitive values should be redacted
        assert "AKIAIOSFODNN7EXAMPLE" not in result.stdout
        assert "user@example.com" not in result.stdout

    def test_redact_flag_explicit(self):
        """--redact should enable redaction."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"
        policy_file = fixtures / "policy_v1.json"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--policy", str(policy_file),
            "--fixed-time", "2025-01-01T00:00:00Z",
            "--redact",
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["redaction_applied"] is True

    def test_no_redact_flag(self):
        """--no-redact should disable redaction."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"
        policy_file = fixtures / "policy_v1.json"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--policy", str(policy_file),
            "--fixed-time", "2025-01-01T00:00:00Z",
            "--no-redact",
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert output["redaction_applied"] is False

        # Raw values should be visible
        assert "AKIAIOSFODNN7EXAMPLE" in result.stdout
        assert "user@example.com" in result.stdout

    def test_redaction_tokens_used(self):
        """Redacted output should use proper tokens."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"
        policy_file = fixtures / "policy_v1.json"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--policy", str(policy_file),
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode == 0

        # Should contain redaction tokens
        assert "[REDACTED_KEY]" in result.stdout or "[REDACTED_EMAIL]" in result.stdout or "[REDACTED_TOKEN]" in result.stdout
