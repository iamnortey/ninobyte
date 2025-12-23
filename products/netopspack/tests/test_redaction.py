"""
Redaction tests for NetOpsPack.

Verifies that sensitive data is properly redacted.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from netopspack.redact import redact_line, redact_text, RedactionStats


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def netopspack_dir() -> Path:
    """Path to netopspack package."""
    return Path(__file__).parent.parent


class TestRedactLine:
    """Tests for redact_line function."""

    def test_redact_ipv4(self):
        """IPv4 addresses are redacted."""
        line = "Connection from 192.168.1.100 established"
        result = redact_line(line)
        assert "[REDACTED_IP]" in result
        assert "192.168.1.100" not in result

    def test_redact_multiple_ips(self):
        """Multiple IPs are redacted."""
        line = "192.168.1.1 connected to 10.0.0.50"
        stats = RedactionStats()
        result = redact_line(line, stats)
        assert result.count("[REDACTED_IP]") == 2
        assert stats.ips == 2

    def test_redact_bearer_token(self):
        """Bearer tokens are redacted."""
        line = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = redact_line(line)
        assert "[REDACTED_TOKEN]" in result
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result

    def test_redact_api_key(self):
        """API keys are redacted."""
        line = "api_key=sk_live_abc123xyz789"
        result = redact_line(line)
        assert "[REDACTED_KEY]" in result
        assert "sk_live_abc123xyz789" not in result

    def test_redact_email(self):
        """Email addresses are redacted."""
        line = "User login: user@example.com"
        stats = RedactionStats()
        result = redact_line(line, stats)
        assert "[REDACTED_EMAIL]" in result
        assert "user@example.com" not in result
        assert stats.emails == 1

    def test_redact_aws_key(self):
        """AWS access keys are redacted."""
        line = "AWS key: AKIAIOSFODNN7EXAMPLE"
        result = redact_line(line)
        assert "[REDACTED_AWS]" in result
        assert "AKIAIOSFODNN7EXAMPLE" not in result

    def test_redact_long_hex(self):
        """Long hex strings are redacted."""
        line = "Token: 0123456789abcdef0123456789abcdef"
        result = redact_line(line)
        assert "[REDACTED_HEX]" in result
        assert "0123456789abcdef0123456789abcdef" not in result

    def test_stats_tracking(self):
        """Redaction stats are tracked correctly."""
        lines = [
            "IP: 192.168.1.1",
            "Email: test@example.com",
            "Token: Bearer abc123",
        ]
        stats = RedactionStats()
        for line in lines:
            redact_line(line, stats)

        assert stats.ips == 1
        assert stats.emails == 1
        assert stats.tokens == 1


class TestRedactText:
    """Tests for redact_text function."""

    def test_redact_multiline(self):
        """Multiline text is redacted."""
        text = "IP: 192.168.1.1\nEmail: test@example.com"
        result, stats = redact_text(text)
        assert "[REDACTED_IP]" in result
        assert "[REDACTED_EMAIL]" in result
        assert stats.ips == 1
        assert stats.emails == 1


class TestCLIRedaction:
    """Tests for CLI redaction behavior."""

    def _run_diagnose(
        self,
        netopspack_dir: Path,
        input_path: Path,
        format: str,
        redact: bool = True,
    ) -> str:
        """Run diagnose command and return output."""
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
        if not redact:
            cmd.append("--no-redact")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=netopspack_dir,
            env={
                **dict(__import__("os").environ),
                "PYTHONPATH": str(netopspack_dir / "src"),
            },
        )
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        return result.stdout

    def test_redaction_enabled_by_default(self, fixtures_dir: Path, netopspack_dir: Path):
        """Redaction is enabled by default."""
        input_path = fixtures_dir / "redaction_test.log"
        output = self._run_diagnose(netopspack_dir, input_path, "syslog")
        report = json.loads(output)

        assert report["redaction_applied"] is True
        # Check IPs are redacted
        output_str = json.dumps(report)
        assert "192.168.1.100" not in output_str
        assert "[REDACTED_IP]" in output_str

    def test_redaction_disabled_with_no_redact(self, fixtures_dir: Path, netopspack_dir: Path):
        """--no-redact disables redaction."""
        input_path = fixtures_dir / "redaction_test.log"
        output = self._run_diagnose(netopspack_dir, input_path, "syslog", redact=False)
        report = json.loads(output)

        assert report["redaction_applied"] is False
        # Check IPs are NOT redacted
        output_str = json.dumps(report)
        assert "192.168.1.100" in output_str

    def test_redaction_summary_in_output(self, fixtures_dir: Path, netopspack_dir: Path):
        """Redaction summary is included in output."""
        input_path = fixtures_dir / "redaction_test.log"
        output = self._run_diagnose(netopspack_dir, input_path, "syslog")
        report = json.loads(output)

        assert "redaction_summary" in report
        summary = report["redaction_summary"]
        assert "ips" in summary
        assert "emails" in summary
        assert "tokens" in summary
        # File has IPs, emails, tokens to redact
        assert summary["ips"] > 0
        assert summary["emails"] > 0

    def test_nginx_ips_redacted(self, fixtures_dir: Path, netopspack_dir: Path):
        """Nginx log IPs are redacted."""
        input_path = fixtures_dir / "sample_nginx.log"
        output = self._run_diagnose(netopspack_dir, input_path, "nginx")
        report = json.loads(output)

        output_str = json.dumps(report)
        # Original IPs should not appear
        assert "192.168.1.1" not in output_str
        assert "10.0.0.50" not in output_str
        # Redacted placeholder should appear
        assert "[REDACTED_IP]" in output_str

    def test_haproxy_ips_redacted(self, fixtures_dir: Path, netopspack_dir: Path):
        """HAProxy log IPs are redacted."""
        input_path = fixtures_dir / "sample_haproxy.log"
        output = self._run_diagnose(netopspack_dir, input_path, "haproxy")
        report = json.loads(output)

        output_str = json.dumps(report)
        assert "192.168.1.1" not in output_str
        assert "[REDACTED_IP]" in output_str
