"""
CompliancePack Repo-Root Invocation Contract Tests.

Contract-grade tests validating that CompliancePack can be invoked
from repo root using PYTHONPATH prefix (no pip install -e . required).

Canonical invocation:
    PYTHONPATH=products/compliancepack/src python3 -m compliancepack check ...
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def get_repo_root() -> Path:
    """Get the monorepo root directory."""
    # tests/test_repo_root_contract.py -> compliancepack -> products -> repo_root
    return Path(__file__).parent.parent.parent.parent


def get_compliancepack_root() -> Path:
    """Get the CompliancePack product root."""
    return get_repo_root() / "products" / "compliancepack"


def run_from_repo_root(*args: str) -> subprocess.CompletedProcess:
    """Run CompliancePack from repo root with PYTHONPATH prefix."""
    repo_root = get_repo_root()
    compliancepack_src = get_compliancepack_root() / "src"

    cmd = [sys.executable, "-m", "compliancepack", *args]
    env = {
        **dict(os.environ),
        "PYTHONPATH": str(compliancepack_src),
    }

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=repo_root,
        env=env,
    )


class TestRepoRootInvocation:
    """Test repo-root invocation contract."""

    def test_help_from_repo_root(self):
        """--help should work from repo root."""
        result = run_from_repo_root("--help")
        assert result.returncode == 0
        assert "compliancepack" in result.stdout.lower()

    def test_check_help_from_repo_root(self):
        """check --help should work from repo root."""
        result = run_from_repo_root("check", "--help")
        assert result.returncode == 0
        assert "--input" in result.stdout
        assert "--pack" in result.stdout
        assert "--fail-on" in result.stdout

    def test_version_from_repo_root(self):
        """--version should work from repo root."""
        result = run_from_repo_root("--version")
        assert result.returncode == 0
        # Version should be present in output
        assert "0." in result.stdout or "1." in result.stdout

    def test_list_packs_from_repo_root(self):
        """--list-packs should work from repo root."""
        result = run_from_repo_root("check", "--list-packs")
        assert result.returncode == 0
        assert "secrets.v1" in result.stdout
        assert "pii.v1" in result.stdout


class TestRepoRootCheckCommand:
    """Test check command from repo root."""

    def test_check_with_pack_from_repo_root(self):
        """check --pack should work from repo root."""
        fixtures = get_compliancepack_root() / "tests" / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_from_repo_root(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        # Exit 0 or 3 are valid
        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)
        assert output["format"] == "compliancepack.check.v1"
        assert output["policy_path"] == "pack:secrets.v1"

    def test_check_with_policy_from_repo_root(self):
        """check --policy should work from repo root."""
        fixtures = get_compliancepack_root() / "tests" / "fixtures"
        input_file = fixtures / "sample_input.txt"
        policy_file = fixtures / "policy_v1.json"

        result = run_from_repo_root(
            "check",
            "--input", str(input_file),
            "--policy", str(policy_file),
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        # Exit 0 or 3 are valid
        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)
        assert output["format"] == "compliancepack.check.v1"

    def test_check_with_fail_on_from_repo_root(self):
        """--fail-on threshold should work from repo root."""
        fixtures = get_compliancepack_root() / "tests" / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_from_repo_root(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fail-on", "critical",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)
        assert output["threshold"]["fail_on"] == "critical"

    def test_check_sariflite_format_from_repo_root(self):
        """--format sariflite should work from repo root."""
        fixtures = get_compliancepack_root() / "tests" / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_from_repo_root(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--format", "compliancepack.sariflite.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)
        assert output["format"] == "compliancepack.sariflite.v1"

    def test_check_exit_zero_from_repo_root(self):
        """--exit-zero should force exit 0 from repo root."""
        fixtures = get_compliancepack_root() / "tests" / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_from_repo_root(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--exit-zero",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        # --exit-zero forces exit 0
        assert result.returncode == 0


class TestRepoRootDeterminism:
    """Test deterministic output from repo root."""

    def test_same_output_multiple_runs(self):
        """Multiple runs from repo root should produce identical output."""
        fixtures = get_compliancepack_root() / "tests" / "fixtures"
        input_file = fixtures / "sample_input.txt"

        outputs = []
        for _ in range(3):
            result = run_from_repo_root(
                "check",
                "--input", str(input_file),
                "--pack", "secrets.v1",
                "--fixed-time", "2025-01-01T00:00:00Z",
            )
            assert result.returncode in (0, 3)
            outputs.append(result.stdout)

        # All outputs should be identical
        assert len(set(outputs)) == 1, "Output should be deterministic"

    def test_exit_code_matches_expected(self):
        """exit_code_expected in output should match actual exit code."""
        fixtures = get_compliancepack_root() / "tests" / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_from_repo_root(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        output = json.loads(result.stdout)
        assert output["exit_code_expected"] == result.returncode


class TestRepoRootErrorCases:
    """Test error cases from repo root."""

    def test_missing_input_file(self):
        """Missing input file should return exit 1."""
        result = run_from_repo_root(
            "check",
            "--input", "/nonexistent/file.txt",
            "--pack", "secrets.v1",
        )
        assert result.returncode == 1
        assert "not found" in result.stderr.lower()

    def test_missing_required_args(self):
        """Missing required args should return exit 2."""
        result = run_from_repo_root("check")
        assert result.returncode == 2

    def test_invalid_pack_name(self):
        """Invalid pack name should return exit 1."""
        fixtures = get_compliancepack_root() / "tests" / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_from_repo_root(
            "check",
            "--input", str(input_file),
            "--pack", "nonexistent.v999",
        )
        assert result.returncode == 1

    def test_invalid_severity(self):
        """Invalid --fail-on severity should return exit 2."""
        fixtures = get_compliancepack_root() / "tests" / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_from_repo_root(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fail-on", "invalid",
        )
        assert result.returncode == 2


class TestRepoRootDirectoryScan:
    """Test directory scanning from repo root."""

    def test_directory_scan_from_repo_root(self):
        """Directory scan should work from repo root."""
        fixtures = get_compliancepack_root() / "tests" / "fixtures"

        result = run_from_repo_root(
            "check",
            "--input", str(fixtures),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)
        assert output["format"] == "compliancepack.check.v1"
        assert "inputs" in output
        assert "scan_stats" in output

    def test_directory_scan_determinism_from_repo_root(self):
        """Directory scan should be deterministic from repo root."""
        fixtures = get_compliancepack_root() / "tests" / "fixtures"

        outputs = []
        for _ in range(3):
            result = run_from_repo_root(
                "check",
                "--input", str(fixtures),
                "--pack", "secrets.v1",
                "--fixed-time", "2025-01-01T00:00:00Z",
            )
            assert result.returncode in (0, 3)
            outputs.append(result.stdout)

        assert len(set(outputs)) == 1, "Directory scan should be deterministic"

    def test_extension_filter_from_repo_root(self):
        """Extension filter should work from repo root."""
        fixtures = get_compliancepack_root() / "tests" / "fixtures"

        result = run_from_repo_root(
            "check",
            "--input", str(fixtures),
            "--pack", "secrets.v1",
            "--include-ext", ".txt",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)
        # Should only scan .txt files
        assert output["scan_stats"]["files_scanned"] >= 1

    def test_max_files_from_repo_root(self):
        """Max files limit should work from repo root."""
        fixtures = get_compliancepack_root() / "tests" / "fixtures"

        result = run_from_repo_root(
            "check",
            "--input", str(fixtures),
            "--pack", "secrets.v1",
            "--max-files", "2",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode in (0, 3)
        output = json.loads(result.stdout)
        assert output["scan_stats"]["files_scanned"] <= 2

    def test_max_bytes_per_file_from_repo_root(self):
        """Max bytes per file should work from repo root."""
        fixtures = get_compliancepack_root() / "tests" / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_from_repo_root(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--max-bytes-per-file", "100",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        # Should still work, just with truncated file content
        assert result.returncode in (0, 3)

    def test_new_cli_flags_in_help(self):
        """New CLI flags should appear in --help."""
        result = run_from_repo_root("check", "--help")

        assert result.returncode == 0
        assert "--max-files" in result.stdout
        assert "--max-bytes-per-file" in result.stdout
        assert "--include-ext" in result.stdout
        assert "--follow-symlinks" in result.stdout
