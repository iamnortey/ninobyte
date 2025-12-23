"""
Signal aggregation tests for NetOpsPack.

Verifies that diagnostic signals are correctly computed.
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


class TestSignalAggregation:
    """Tests for signal aggregation in diagnose output."""

    def _run_diagnose(
        self,
        netopspack_dir: Path,
        input_path: Path,
        format: str,
    ) -> dict:
        """Run diagnose command and return parsed output."""
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
        return json.loads(result.stdout)

    def test_syslog_severity_counts(self, fixtures_dir: Path, netopspack_dir: Path):
        """Syslog severity counts are computed."""
        input_path = fixtures_dir / "sample_syslog.log"
        report = self._run_diagnose(netopspack_dir, input_path, "syslog")

        signals = report["signals"]
        assert "severity_counts" in signals

        severity_counts = signals["severity_counts"]
        # File has info (Accepted), error (refused, Error), warning (warning), critical (critical)
        assert "info" in severity_counts
        assert "error" in severity_counts

    def test_syslog_keyword_hits(self, fixtures_dir: Path, netopspack_dir: Path):
        """Syslog keyword hits are counted."""
        input_path = fixtures_dir / "sample_syslog.log"
        report = self._run_diagnose(netopspack_dir, input_path, "syslog")

        signals = report["signals"]
        assert "keyword_hits" in signals

        keyword_hits = signals["keyword_hits"]
        # File has "refused", "Error", "warning", "critical"
        assert keyword_hits.get("refused", 0) >= 1
        assert keyword_hits.get("error", 0) >= 1

    def test_nginx_status_counts(self, fixtures_dir: Path, netopspack_dir: Path):
        """Nginx status code counts are computed."""
        input_path = fixtures_dir / "sample_nginx.log"
        report = self._run_diagnose(netopspack_dir, input_path, "nginx")

        signals = report["signals"]
        assert "status_counts" in signals

        status_counts = signals["status_counts"]
        # File has 200, 401, 304, 500, 403, 404
        assert "200" in status_counts
        assert "500" in status_counts
        assert "404" in status_counts

    def test_nginx_top_paths(self, fixtures_dir: Path, netopspack_dir: Path):
        """Nginx top paths are computed."""
        input_path = fixtures_dir / "sample_nginx.log"
        report = self._run_diagnose(netopspack_dir, input_path, "nginx")

        signals = report["signals"]
        assert "top_paths" in signals

        top_paths = signals["top_paths"]
        # File has /api/users (twice), /api/login, /api/health, etc.
        assert "/api/users" in top_paths
        assert top_paths["/api/users"] == 2

    def test_nginx_unique_sources(self, fixtures_dir: Path, netopspack_dir: Path):
        """Nginx unique source count is computed."""
        input_path = fixtures_dir / "sample_nginx.log"
        report = self._run_diagnose(netopspack_dir, input_path, "nginx")

        signals = report["signals"]
        assert "unique_sources" in signals
        # File has multiple unique IPs (after redaction, all become [REDACTED_IP])
        # But the count is computed before redaction
        assert signals["unique_sources"] >= 1

    def test_haproxy_status_counts(self, fixtures_dir: Path, netopspack_dir: Path):
        """HAProxy status code counts are computed."""
        input_path = fixtures_dir / "sample_haproxy.log"
        report = self._run_diagnose(netopspack_dir, input_path, "haproxy")

        signals = report["signals"]
        assert "status_counts" in signals

        status_counts = signals["status_counts"]
        # File has 200, 500, 304, 401, 503
        assert "200" in status_counts
        assert "500" in status_counts

    def test_haproxy_severity_counts(self, fixtures_dir: Path, netopspack_dir: Path):
        """HAProxy severity counts are computed."""
        input_path = fixtures_dir / "sample_haproxy.log"
        report = self._run_diagnose(netopspack_dir, input_path, "haproxy")

        signals = report["signals"]
        assert "severity_counts" in signals

        severity_counts = signals["severity_counts"]
        # File has info (200, 304), error (500, 503), warning (401 with CD--)
        assert "info" in severity_counts
        assert "error" in severity_counts

    def test_event_count_matches(self, fixtures_dir: Path, netopspack_dir: Path):
        """Event count matches parsed events."""
        input_path = fixtures_dir / "sample_syslog.log"
        report = self._run_diagnose(netopspack_dir, input_path, "syslog")

        # 10 lines in fixture (after adding sensitive data lines)
        assert report["line_count"] == 10
        assert report["event_count"] == 10

    def test_limit_restricts_events(self, fixtures_dir: Path, netopspack_dir: Path):
        """--limit restricts number of events in output."""
        input_path = fixtures_dir / "sample_nginx.log"

        cmd = [
            sys.executable,
            "-m",
            "netopspack",
            "diagnose",
            "--input",
            str(input_path),
            "--format",
            "nginx",
            "--fixed-time",
            "2025-01-01T00:00:00Z",
            "--limit",
            "3",
        ]

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
        assert result.returncode == 0
        report = json.loads(result.stdout)

        # 10 lines in fixture (after adding sensitive data lines), but limit is 3
        assert report["event_count"] == 10
        assert len(report["events"]) == 3
        assert report["limit"] == 3
