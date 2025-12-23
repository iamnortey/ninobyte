"""
Leakage-is-blocker tests for NetOpsPack.

These tests verify that sensitive data is NEVER leaked in JSON outputs
when redaction is enabled (the default). Any leakage is treated as a
release-blocking defect.

Tests use subprocess-level invocation to match production behavior.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


# Controlled sensitive test data that MUST be redacted
# These values are planted in the fixtures and must NEVER appear in redacted output
SENSITIVE_DATA = {
    "ip": "203.0.113.10",
    "email": "user@example.com",
    "aws_key": "AKIAIOSFODNN7EXAMPLE",
    "jwt_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
}

# Expected redaction placeholders
REDACTION_PLACEHOLDERS = [
    "[REDACTED_IP]",
    "[REDACTED_EMAIL]",
    "[REDACTED_AWS_KEY]",
    "[REDACTED_TOKEN]",
]


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def netopspack_dir() -> Path:
    """Path to netopspack package."""
    return Path(__file__).parent.parent


def _run_diagnose(
    netopspack_dir: Path,
    input_path: Path,
    format: str,
    no_redact: bool = False,
    redact_explicit: bool = False,
) -> subprocess.CompletedProcess:
    """
    Run diagnose command via subprocess.

    Args:
        netopspack_dir: Path to the netopspack package root
        input_path: Path to input log file
        format: Log format (syslog, nginx, haproxy)
        no_redact: If True, add --no-redact flag
        redact_explicit: If True, add --redact flag

    Returns:
        CompletedProcess with captured output
    """
    cmd = [
        sys.executable,
        "-m",
        "netopspack",
        "diagnose",
        "--input",
        str(input_path),
        "--format",
        format,
        "--fixed-time",
        "2025-01-01T00:00:00Z",
    ]

    if no_redact:
        cmd.append("--no-redact")
    if redact_explicit:
        cmd.append("--redact")

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=netopspack_dir,
        env={
            **dict(os.environ),
            "PYTHONPATH": str(netopspack_dir / "src"),
        },
    )


class TestLeakageBlocker:
    """
    Tests that verify no sensitive data leaks in redacted output.

    These are release-blocking tests - any failure means sensitive data
    could leak to users and must be fixed before release.
    """

    @pytest.mark.parametrize(
        "format,fixture",
        [
            ("syslog", "sample_syslog.log"),
            ("nginx", "sample_nginx.log"),
            ("haproxy", "sample_haproxy.log"),
        ],
    )
    def test_default_redaction_no_ip_leakage(
        self, format: str, fixture: str, fixtures_dir: Path, netopspack_dir: Path
    ):
        """Default redaction (ON) must not leak IP addresses."""
        result = _run_diagnose(
            netopspack_dir, fixtures_dir / fixture, format
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # The sensitive IP must NOT appear in output
        assert SENSITIVE_DATA["ip"] not in result.stdout, (
            f"LEAKAGE DETECTED: IP address {SENSITIVE_DATA['ip']} found in {format} output"
        )

        # The redaction placeholder MUST appear
        assert "[REDACTED_IP]" in result.stdout, (
            f"Missing IP redaction placeholder in {format} output"
        )

    @pytest.mark.parametrize(
        "format,fixture",
        [
            ("syslog", "sample_syslog.log"),
            ("nginx", "sample_nginx.log"),
            ("haproxy", "sample_haproxy.log"),
        ],
    )
    def test_default_redaction_no_email_leakage(
        self, format: str, fixture: str, fixtures_dir: Path, netopspack_dir: Path
    ):
        """Default redaction (ON) must not leak email addresses."""
        result = _run_diagnose(
            netopspack_dir, fixtures_dir / fixture, format
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # The sensitive email must NOT appear in output
        assert SENSITIVE_DATA["email"] not in result.stdout, (
            f"LEAKAGE DETECTED: Email {SENSITIVE_DATA['email']} found in {format} output"
        )

        # The redaction placeholder MUST appear
        assert "[REDACTED_EMAIL]" in result.stdout, (
            f"Missing email redaction placeholder in {format} output"
        )

    @pytest.mark.parametrize(
        "format,fixture",
        [
            ("syslog", "sample_syslog.log"),
            ("nginx", "sample_nginx.log"),
            ("haproxy", "sample_haproxy.log"),
        ],
    )
    def test_default_redaction_no_aws_key_leakage(
        self, format: str, fixture: str, fixtures_dir: Path, netopspack_dir: Path
    ):
        """Default redaction (ON) must not leak AWS access keys."""
        result = _run_diagnose(
            netopspack_dir, fixtures_dir / fixture, format
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # The sensitive AWS key must NOT appear in output
        assert SENSITIVE_DATA["aws_key"] not in result.stdout, (
            f"LEAKAGE DETECTED: AWS key {SENSITIVE_DATA['aws_key']} found in {format} output"
        )

        # The redaction placeholder MUST appear
        assert "[REDACTED_AWS_KEY]" in result.stdout, (
            f"Missing AWS key redaction placeholder in {format} output"
        )

    @pytest.mark.parametrize(
        "format,fixture",
        [
            ("syslog", "sample_syslog.log"),
            ("nginx", "sample_nginx.log"),
            ("haproxy", "sample_haproxy.log"),
        ],
    )
    def test_default_redaction_no_jwt_leakage(
        self, format: str, fixture: str, fixtures_dir: Path, netopspack_dir: Path
    ):
        """Default redaction (ON) must not leak JWT tokens."""
        result = _run_diagnose(
            netopspack_dir, fixtures_dir / fixture, format
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # The sensitive JWT must NOT appear in output
        assert SENSITIVE_DATA["jwt_token"] not in result.stdout, (
            f"LEAKAGE DETECTED: JWT token found in {format} output"
        )

        # The redaction placeholder MUST appear (either from JWT or Bearer pattern)
        assert "[REDACTED_TOKEN]" in result.stdout, (
            f"Missing token redaction placeholder in {format} output"
        )

    @pytest.mark.parametrize(
        "format,fixture",
        [
            ("syslog", "sample_syslog.log"),
            ("nginx", "sample_nginx.log"),
            ("haproxy", "sample_haproxy.log"),
        ],
    )
    def test_default_redaction_applied_flag_true(
        self, format: str, fixture: str, fixtures_dir: Path, netopspack_dir: Path
    ):
        """Default redaction produces redaction_applied: true in output."""
        result = _run_diagnose(
            netopspack_dir, fixtures_dir / fixture, format
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        report = json.loads(result.stdout)
        assert report["redaction_applied"] is True, (
            f"redaction_applied must be true by default for {format}"
        )


class TestExplicitOptOut:
    """
    Tests that verify --no-redact correctly disables redaction.

    These tests confirm that users can explicitly opt out and see raw data.
    """

    @pytest.mark.parametrize(
        "format,fixture",
        [
            ("syslog", "sample_syslog.log"),
            ("nginx", "sample_nginx.log"),
            ("haproxy", "sample_haproxy.log"),
        ],
    )
    def test_no_redact_shows_sensitive_data(
        self, format: str, fixture: str, fixtures_dir: Path, netopspack_dir: Path
    ):
        """--no-redact must show sensitive data in output."""
        result = _run_diagnose(
            netopspack_dir, fixtures_dir / fixture, format, no_redact=True
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # With --no-redact, sensitive data MUST appear in output
        assert SENSITIVE_DATA["ip"] in result.stdout, (
            f"IP address should be visible with --no-redact in {format}"
        )
        assert SENSITIVE_DATA["email"] in result.stdout, (
            f"Email should be visible with --no-redact in {format}"
        )
        assert SENSITIVE_DATA["aws_key"] in result.stdout, (
            f"AWS key should be visible with --no-redact in {format}"
        )

    @pytest.mark.parametrize(
        "format,fixture",
        [
            ("syslog", "sample_syslog.log"),
            ("nginx", "sample_nginx.log"),
            ("haproxy", "sample_haproxy.log"),
        ],
    )
    def test_no_redact_applied_flag_false(
        self, format: str, fixture: str, fixtures_dir: Path, netopspack_dir: Path
    ):
        """--no-redact produces redaction_applied: false in output."""
        result = _run_diagnose(
            netopspack_dir, fixtures_dir / fixture, format, no_redact=True
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        report = json.loads(result.stdout)
        assert report["redaction_applied"] is False, (
            f"redaction_applied must be false with --no-redact for {format}"
        )


class TestMutualExclusion:
    """
    Tests that verify --redact and --no-redact cannot be used together.
    """

    def test_mutual_exclusion_both_flags_exit_2(
        self, fixtures_dir: Path, netopspack_dir: Path
    ):
        """Using both --redact and --no-redact must exit with code 2."""
        cmd = [
            sys.executable,
            "-m",
            "netopspack",
            "diagnose",
            "--input",
            str(fixtures_dir / "sample_syslog.log"),
            "--format",
            "syslog",
            "--redact",
            "--no-redact",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=netopspack_dir,
            env={
                **dict(os.environ),
                "PYTHONPATH": str(netopspack_dir / "src"),
            },
        )

        assert result.returncode == 2, (
            f"Expected exit code 2 for mutual exclusion, got {result.returncode}"
        )

    def test_mutual_exclusion_error_message(
        self, fixtures_dir: Path, netopspack_dir: Path
    ):
        """Mutual exclusion error message mentions conflicting options."""
        cmd = [
            sys.executable,
            "-m",
            "netopspack",
            "diagnose",
            "--input",
            str(fixtures_dir / "sample_syslog.log"),
            "--format",
            "syslog",
            "--redact",
            "--no-redact",
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=netopspack_dir,
            env={
                **dict(os.environ),
                "PYTHONPATH": str(netopspack_dir / "src"),
            },
        )

        # argparse mutual exclusion error mentions "not allowed"
        assert "not allowed" in result.stderr.lower(), (
            f"Expected mutual exclusion error message, got: {result.stderr}"
        )


class TestExplicitRedactFlag:
    """
    Tests that verify --redact works correctly (same as default).
    """

    @pytest.mark.parametrize(
        "format,fixture",
        [
            ("syslog", "sample_syslog.log"),
            ("nginx", "sample_nginx.log"),
            ("haproxy", "sample_haproxy.log"),
        ],
    )
    def test_explicit_redact_no_leakage(
        self, format: str, fixture: str, fixtures_dir: Path, netopspack_dir: Path
    ):
        """Explicit --redact must not leak sensitive data (same as default)."""
        result = _run_diagnose(
            netopspack_dir, fixtures_dir / fixture, format, redact_explicit=True
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Sensitive data must NOT appear
        for key, value in SENSITIVE_DATA.items():
            assert value not in result.stdout, (
                f"LEAKAGE DETECTED: {key} found in {format} output with --redact"
            )

        # Report must show redaction was applied
        report = json.loads(result.stdout)
        assert report["redaction_applied"] is True


class TestRedactionCoverage:
    """
    Tests that verify all expected redaction patterns are applied.
    """

    def test_redaction_summary_counts(
        self, fixtures_dir: Path, netopspack_dir: Path
    ):
        """Redaction summary must have non-zero counts for planted data."""
        result = _run_diagnose(
            netopspack_dir, fixtures_dir / "sample_syslog.log", "syslog"
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        report = json.loads(result.stdout)
        summary = report["redaction_summary"]

        # The syslog fixture has IPs, email, AWS key, and tokens
        assert summary["ips"] > 0, "Expected IP redactions"
        assert summary["emails"] > 0, "Expected email redactions"
        assert summary["keys"] > 0, "Expected AWS key redactions"
        assert summary["tokens"] > 0, "Expected token redactions"

    def test_all_string_fields_redacted(
        self, fixtures_dir: Path, netopspack_dir: Path
    ):
        """All string fields in events must be redacted."""
        result = _run_diagnose(
            netopspack_dir, fixtures_dir / "sample_nginx.log", "nginx"
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        report = json.loads(result.stdout)

        # Check each event
        for event in report["events"]:
            # The 'source' field should be redacted (was IP)
            if "source" in event:
                assert SENSITIVE_DATA["ip"] not in str(event["source"]), (
                    f"IP leaked in source field: {event['source']}"
                )

            # The 'raw' field should be redacted
            if "raw" in event:
                for key, value in SENSITIVE_DATA.items():
                    assert value not in event["raw"], (
                        f"{key} leaked in raw field"
                    )

            # The 'message' field should be redacted
            if "message" in event:
                for key, value in SENSITIVE_DATA.items():
                    assert value not in event["message"], (
                        f"{key} leaked in message field"
                    )


class TestRedactionTestFixture:
    """
    Tests specifically for the redaction_test.log fixture.
    """

    def test_redaction_test_fixture_all_patterns(
        self, fixtures_dir: Path, netopspack_dir: Path
    ):
        """redaction_test.log fixture tests all redaction patterns."""
        result = _run_diagnose(
            netopspack_dir, fixtures_dir / "redaction_test.log", "syslog"
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Check no sensitive data leaks
        sensitive_in_fixture = [
            "192.168.1.100",
            "user@example.com",
            "AKIAIOSFODNN7EXAMPLE",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "2001:db8::1",
            "0123456789abcdef0123456789abcdef",
        ]

        for sensitive in sensitive_in_fixture:
            assert sensitive not in result.stdout, (
                f"LEAKAGE DETECTED: {sensitive} found in output"
            )

        # All placeholders should be present
        expected_placeholders = [
            "[REDACTED_IP]",
            "[REDACTED_EMAIL]",
            "[REDACTED_AWS_KEY]",
            "[REDACTED_TOKEN]",
            "[REDACTED_HEX]",
        ]

        for placeholder in expected_placeholders:
            assert placeholder in result.stdout, (
                f"Missing placeholder: {placeholder}"
            )
