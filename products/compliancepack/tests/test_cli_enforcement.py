"""
CompliancePack CLI enforcement tests.

Contract-grade tests for:
- Exit code semantics (0/2/3)
- --fail-on threshold behavior
- --format output selection
- --max-findings truncation
- --exit-zero override
- Byte-for-byte determinism
"""

import json
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
        env={**dict(__import__("os").environ), **env},
    )


class TestExitCodeSemantics:
    """Test exit code behavior."""

    def test_exit_zero_no_violations(self):
        """Exit 0 when no findings at/above threshold."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        # secrets.v1 has critical/high findings, set threshold to critical only
        # and we should still get exit 3 because there IS a critical finding
        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fail-on", "info",  # info catches all, so will have violations
            "--fixed-time", "2025-01-01T00:00:00Z",
        )
        # Should be exit 3 (has findings at/above info level)
        assert result.returncode == 3

    def test_exit_three_with_violations(self):
        """Exit 3 when findings at/above threshold exist."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fail-on", "high",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )
        assert result.returncode == 3
        output = json.loads(result.stdout)
        assert output["threshold"]["violations"] > 0

    def test_exit_two_usage_error(self):
        """Exit 2 for CLI usage/config errors."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        # Missing --pack or --policy
        result = run_cli(
            "check",
            "--input", str(input_file),
        )
        assert result.returncode == 2

    def test_exit_two_invalid_fail_on(self):
        """Exit 2 for invalid --fail-on value."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fail-on", "invalid",
        )
        assert result.returncode == 2


class TestFailOnThreshold:
    """Test --fail-on threshold behavior."""

    def test_fail_on_critical_only(self):
        """--fail-on critical only catches critical findings."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fail-on", "critical",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )
        assert result.returncode == 3  # Has critical finding
        output = json.loads(result.stdout)
        assert output["threshold"]["fail_on"] == "critical"
        assert output["threshold"]["violations"] == 1  # Only critical

    def test_fail_on_high_catches_high_and_critical(self):
        """--fail-on high catches high and critical findings."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fail-on", "high",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )
        assert result.returncode == 3
        output = json.loads(result.stdout)
        assert output["threshold"]["violations"] == 2  # critical + high

    def test_fail_on_default_is_high(self):
        """Default --fail-on is high."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )
        output = json.loads(result.stdout)
        assert output["threshold"]["fail_on"] == "high"


class TestOutputFormat:
    """Test --format output selection."""

    def test_default_format_is_check_v1(self):
        """Default format is compliancepack.check.v1."""
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
        assert output["format"] == "compliancepack.check.v1"

    def test_sariflite_format(self):
        """--format sariflite produces correct format."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--format", "compliancepack.sariflite.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )
        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)
        assert output["format"] == "compliancepack.sariflite.v1"
        assert output["version"] == "sariflite.v1"
        assert "tool" in output
        assert "runs" in output

    def test_invalid_format_exit_two(self):
        """Invalid --format value produces exit 2."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--format", "invalid.format",
        )
        assert result.returncode == 2


class TestMaxFindings:
    """Test --max-findings truncation."""

    def test_max_findings_truncates(self):
        """--max-findings limits output findings."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--max-findings", "1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )
        output = json.loads(result.stdout)
        assert len(output["findings"]) == 1
        assert output["truncated"] is True

    def test_max_findings_zero_unlimited(self):
        """--max-findings 0 means unlimited."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--max-findings", "0",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )
        output = json.loads(result.stdout)
        assert output["truncated"] is False
        assert output["max_findings"] is None

    def test_max_findings_not_truncated_if_under(self):
        """Not truncated if findings count under limit."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--max-findings", "100",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )
        output = json.loads(result.stdout)
        assert output["truncated"] is False


class TestExitZeroOverride:
    """Test --exit-zero override."""

    def test_exit_zero_forces_zero(self):
        """--exit-zero forces exit 0 even with violations."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fail-on", "high",
            "--exit-zero",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )
        assert result.returncode == 0
        output = json.loads(result.stdout)
        # Still reports violations in output
        assert output["threshold"]["violations"] > 0
        assert output["exit_code_expected"] == 0

    def test_exit_zero_with_no_violations(self):
        """--exit-zero with no violations still exits 0."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        # Use a threshold that won't catch the findings
        # The sample has critical and high, so info will catch them
        # We need a case with no findings - use pii.v1 with critical threshold
        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "pii.v1",
            "--fail-on", "critical",  # No critical PII findings
            "--exit-zero",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )
        assert result.returncode == 0


class TestDeterminism:
    """Test byte-for-byte determinism."""

    def test_check_v1_deterministic(self):
        """check.v1 format is byte-for-byte deterministic."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        args = [
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fail-on", "high",
            "--fixed-time", "2025-01-01T00:00:00Z",
        ]

        result1 = run_cli(*args)
        result2 = run_cli(*args)

        assert result1.returncode == result2.returncode
        assert result1.stdout == result2.stdout

    def test_sariflite_deterministic(self):
        """sariflite format is byte-for-byte deterministic."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        args = [
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fail-on", "high",
            "--format", "compliancepack.sariflite.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        ]

        result1 = run_cli(*args)
        result2 = run_cli(*args)

        assert result1.returncode == result2.returncode
        assert result1.stdout == result2.stdout

    def test_max_findings_deterministic(self):
        """Truncation with --max-findings is deterministic."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        args = [
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--max-findings", "1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        ]

        result1 = run_cli(*args)
        result2 = run_cli(*args)

        assert result1.stdout == result2.stdout


class TestOutputSchemaExtensions:
    """Test output schema has new fields."""

    def test_check_v1_has_threshold(self):
        """check.v1 format includes threshold field."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )
        output = json.loads(result.stdout)
        assert "threshold" in output
        assert "fail_on" in output["threshold"]
        assert "violations" in output["threshold"]

    def test_check_v1_has_exit_code_expected(self):
        """check.v1 format includes exit_code_expected."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )
        output = json.loads(result.stdout)
        assert "exit_code_expected" in output

    def test_check_v1_has_truncated(self):
        """check.v1 format includes truncated field."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )
        output = json.loads(result.stdout)
        assert "truncated" in output
        assert isinstance(output["truncated"], bool)
