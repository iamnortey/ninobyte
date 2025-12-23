"""
Determinism tests for OpsPack.

Verifies that outputs are byte-for-byte identical for the same inputs.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

OPSPACK_DIR = Path(__file__).parent.parent


class TestJSONDeterminism:
    """Test that JSON output is deterministic."""

    def test_same_input_same_output(self, tmp_path):
        """Same input file should produce byte-for-byte identical JSON."""
        # Create test input
        test_file = tmp_path / "incident.log"
        test_file.write_text(
            "2024-01-15T10:30:00Z ERROR Connection failed\n"
            "2024-01-15T10:30:01Z ERROR Timeout occurred\n"
            "192.168.1.1 - User request from token AKIAIOSFODNN7EXAMPLE\n"
        )

        # Run triage twice with fixed time
        def run_triage():
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
            return result.stdout

        output1 = run_triage()
        output2 = run_triage()

        # Must be byte-for-byte identical
        assert output1 == output2, "Output should be deterministic"

    def test_json_keys_sorted(self, tmp_path):
        """JSON output should have sorted keys."""
        test_file = tmp_path / "test.log"
        test_file.write_text("ERROR test\n")

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

        # Parse and verify key order
        data = json.loads(result.stdout)
        keys = list(data.keys())

        # Keys should be sorted alphabetically
        assert keys == sorted(keys), "Top-level keys should be sorted"

        # Signals keys should also be sorted
        signals_keys = list(data["signals"].keys())
        assert signals_keys == sorted(signals_keys), "Signal keys should be sorted"

    def test_signals_lists_sorted(self, tmp_path):
        """Signal lists should be sorted for determinism."""
        test_file = tmp_path / "test.log"
        test_file.write_text(
            "FATAL error first\n"
            "ERROR came second\n"
            "CRITICAL was third\n"
        )

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

        data = json.loads(result.stdout)
        keywords = data["signals"]["error_keywords"]

        # Should be sorted alphabetically
        assert keywords == sorted(keywords), "Error keywords should be sorted"


class TestMultipleRunsConsistency:
    """Test consistency across multiple runs."""

    def test_ten_runs_identical(self, tmp_path):
        """Ten consecutive runs should produce identical output."""
        test_file = tmp_path / "multi.log"
        test_file.write_text(
            "2024-01-15T10:30:00Z ERROR Database connection failed\n"
            "Stack trace:\n"
            '  File "app.py", line 42\n'
            "IP: 10.0.0.1\n"
            "Token: xoxb-test-token-value\n"
        )

        outputs = []
        for _ in range(10):
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
            outputs.append(result.stdout)

        # All outputs should be identical
        assert len(set(outputs)) == 1, "All 10 runs should produce identical output"


class TestSchemaStability:
    """Test that schema structure is stable."""

    def test_required_fields_present(self, tmp_path):
        """All required fields should be present in output."""
        test_file = tmp_path / "test.log"
        test_file.write_text("Simple log line\n")

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

        data = json.loads(result.stdout)

        # Required top-level fields
        required = [
            "schema_version",
            "generated_at_utc",
            "input_path",
            "input_path_type",
            "redaction_applied",
            "signals",
            "line_count",
            "char_count",
            "summary",
        ]
        for field in required:
            assert field in data, f"Required field '{field}' missing"

        # Required signal fields
        signal_fields = ["timestamps", "error_keywords", "stacktrace_markers"]
        for field in signal_fields:
            assert field in data["signals"], f"Required signal field '{field}' missing"
