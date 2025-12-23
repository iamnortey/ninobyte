"""
Determinism tests for NetOpsPack.

Verifies that output is byte-for-byte identical when run with --fixed-time.
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


class TestDeterministicOutput:
    """Tests for deterministic JSON output."""

    def _run_diagnose(
        self,
        netopspack_dir: Path,
        input_path: Path,
        format: str,
        fixed_time: str,
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
            fixed_time,
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

    def test_syslog_determinism(self, fixtures_dir: Path, netopspack_dir: Path):
        """Syslog output is deterministic with --fixed-time."""
        input_path = fixtures_dir / "sample_syslog.log"
        fixed_time = "2025-01-01T00:00:00Z"

        output1 = self._run_diagnose(netopspack_dir, input_path, "syslog", fixed_time)
        output2 = self._run_diagnose(netopspack_dir, input_path, "syslog", fixed_time)

        assert output1 == output2, "Output is not deterministic"

    def test_nginx_determinism(self, fixtures_dir: Path, netopspack_dir: Path):
        """Nginx output is deterministic with --fixed-time."""
        input_path = fixtures_dir / "sample_nginx.log"
        fixed_time = "2025-01-01T00:00:00Z"

        output1 = self._run_diagnose(netopspack_dir, input_path, "nginx", fixed_time)
        output2 = self._run_diagnose(netopspack_dir, input_path, "nginx", fixed_time)

        assert output1 == output2, "Output is not deterministic"

    def test_haproxy_determinism(self, fixtures_dir: Path, netopspack_dir: Path):
        """HAProxy output is deterministic with --fixed-time."""
        input_path = fixtures_dir / "sample_haproxy.log"
        fixed_time = "2025-01-01T00:00:00Z"

        output1 = self._run_diagnose(netopspack_dir, input_path, "haproxy", fixed_time)
        output2 = self._run_diagnose(netopspack_dir, input_path, "haproxy", fixed_time)

        assert output1 == output2, "Output is not deterministic"

    def test_output_has_sorted_keys(self, fixtures_dir: Path, netopspack_dir: Path):
        """Output JSON has sorted keys."""
        input_path = fixtures_dir / "sample_syslog.log"
        fixed_time = "2025-01-01T00:00:00Z"

        output = self._run_diagnose(netopspack_dir, input_path, "syslog", fixed_time)
        report = json.loads(output)

        # Check top-level keys are sorted
        keys = list(report.keys())
        assert keys == sorted(keys), "Top-level keys are not sorted"

        # Check signals keys are sorted
        if "signals" in report:
            signal_keys = list(report["signals"].keys())
            assert signal_keys == sorted(signal_keys), "Signal keys are not sorted"

    def test_fixed_time_in_output(self, fixtures_dir: Path, netopspack_dir: Path):
        """Fixed time appears in output."""
        input_path = fixtures_dir / "sample_syslog.log"
        fixed_time = "2025-01-01T00:00:00Z"

        output = self._run_diagnose(netopspack_dir, input_path, "syslog", fixed_time)
        report = json.loads(output)

        assert report["generated_at_utc"] == fixed_time

    def test_schema_version_present(self, fixtures_dir: Path, netopspack_dir: Path):
        """Schema version is present in output."""
        input_path = fixtures_dir / "sample_syslog.log"
        fixed_time = "2025-01-01T00:00:00Z"

        output = self._run_diagnose(netopspack_dir, input_path, "syslog", fixed_time)
        report = json.loads(output)

        assert "schema_version" in report
        assert report["schema_version"] == "1.0.0"

    def test_redact_flag_determinism(self, fixtures_dir: Path, netopspack_dir: Path):
        """Output is deterministic with and without redaction."""
        input_path = fixtures_dir / "sample_syslog.log"
        fixed_time = "2025-01-01T00:00:00Z"

        # With redaction
        output1 = self._run_diagnose(
            netopspack_dir, input_path, "syslog", fixed_time, redact=True
        )
        output2 = self._run_diagnose(
            netopspack_dir, input_path, "syslog", fixed_time, redact=True
        )
        assert output1 == output2

        # Without redaction
        output3 = self._run_diagnose(
            netopspack_dir, input_path, "syslog", fixed_time, redact=False
        )
        output4 = self._run_diagnose(
            netopspack_dir, input_path, "syslog", fixed_time, redact=False
        )
        assert output3 == output4

        # Different with/without redaction (file has IPs to redact)
        assert output1 != output3
