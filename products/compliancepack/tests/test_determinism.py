"""
CompliancePack Determinism Tests.

Validates byte-for-byte identical output with --fixed-time.
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


class TestDeterministicOutput:
    """Tests for deterministic output."""

    def test_same_input_same_output(self):
        """Same input + fixed-time should produce identical output."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"
        policy_file = fixtures / "policy_v1.json"

        result1 = run_cli(
            "check",
            "--input", str(input_file),
            "--policy", str(policy_file),
            "--fixed-time", "2025-01-01T00:00:00Z",
        )
        result2 = run_cli(
            "check",
            "--input", str(input_file),
            "--policy", str(policy_file),
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        # Exit code 0 or 3 are valid (3 = findings found)
        assert result1.returncode in (0, 3)
        assert result2.returncode in (0, 3)
        assert result1.stdout == result2.stdout, "Output should be byte-for-byte identical"

    def test_multiple_runs_identical(self):
        """Multiple runs should produce identical output."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"
        policy_file = fixtures / "policy_v1.json"

        outputs = []
        for _ in range(5):
            result = run_cli(
                "check",
                "--input", str(input_file),
                "--policy", str(policy_file),
                "--fixed-time", "2025-01-01T00:00:00Z",
            )
            # Exit code 0 or 3 are valid (3 = findings found)
            assert result.returncode in (0, 3)
            outputs.append(result.stdout)

        # All outputs should be identical
        assert len(set(outputs)) == 1, "All outputs should be identical"

    def test_output_is_valid_json(self):
        """Output should be valid JSON."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"
        policy_file = fixtures / "policy_v1.json"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--policy", str(policy_file),
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        # Exit code 0 or 3 are valid (3 = findings found)
        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)
        assert output["format"] == "compliancepack.check.v1"

    def test_json_keys_sorted(self):
        """JSON keys should be sorted for determinism."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"
        policy_file = fixtures / "policy_v1.json"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--policy", str(policy_file),
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        # Exit code 0 or 3 are valid (3 = findings found)
        assert result.returncode in (0, 3)

        # Parse and re-serialize with sort_keys=True
        output = json.loads(result.stdout)
        reserialized = json.dumps(output, sort_keys=True, separators=(",", ": "))

        # Original output should already be sorted
        assert result.stdout.strip() == reserialized

    def test_findings_order_deterministic(self):
        """Findings should always be in the same order."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"
        policy_file = fixtures / "policy_v1.json"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--policy", str(policy_file),
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        # Exit code 0 or 3 are valid (3 = findings found)
        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)

        # Findings should be sorted by severity then id
        findings = output["findings"]
        for i in range(len(findings) - 1):
            current = findings[i]
            next_f = findings[i + 1]
            # Current should be >= next in severity order (lower rank = more severe)
            from compliancepack.policy import get_severity_rank
            current_rank = get_severity_rank(current["severity"])
            next_rank = get_severity_rank(next_f["severity"])
            if current_rank == next_rank:
                assert current["id"] <= next_f["id"], "Same severity should be sorted by id"
            else:
                assert current_rank < next_rank, "Higher severity should come first"

    def test_samples_order_deterministic(self):
        """Samples within a finding should always be in the same order."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"
        policy_file = fixtures / "policy_v1.json"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--policy", str(policy_file),
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        # Exit code 0 or 3 are valid (3 = findings found)
        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)

        for finding in output["findings"]:
            samples = finding["samples"]
            for i in range(len(samples) - 1):
                current = samples[i]
                next_s = samples[i + 1]
                # Samples should be sorted by line, then col_start
                if current["line"] == next_s["line"]:
                    assert current["col_start"] <= next_s["col_start"]
                else:
                    assert current["line"] < next_s["line"]
