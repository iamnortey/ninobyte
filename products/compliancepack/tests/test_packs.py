"""
CompliancePack pack resolver tests.

Tests for:
- list_packs() stable ordering
- load_pack() validation and loading
- Pack name validation (path traversal prevention)
- CLI --list-packs and --pack integration
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from compliancepack.packs import (
    PackError,
    _validate_pack_name,
    get_pack_path,
    list_packs,
    load_pack,
)


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


class TestListPacks:
    """Tests for list_packs() function."""

    def test_list_packs_returns_list(self):
        """list_packs should return a list."""
        packs = list_packs()
        assert isinstance(packs, list)

    def test_list_packs_contains_expected(self):
        """list_packs should contain built-in packs."""
        packs = list_packs()
        assert "secrets.v1" in packs
        assert "pii.v1" in packs

    def test_list_packs_stable_ordering(self):
        """list_packs should return deterministic sorted order."""
        packs1 = list_packs()
        packs2 = list_packs()
        assert packs1 == packs2
        assert packs1 == sorted(packs1)

    def test_list_packs_no_json_extension(self):
        """list_packs should return names without .json extension."""
        packs = list_packs()
        for pack in packs:
            assert not pack.endswith(".json")


class TestLoadPack:
    """Tests for load_pack() function."""

    def test_load_pack_secrets(self):
        """load_pack('secrets.v1') should return valid policy."""
        policy = load_pack("secrets.v1")
        assert policy["schema_version"] == "1.0"
        assert "policies" in policy
        assert len(policy["policies"]) > 0

        # Check expected policy IDs
        policy_ids = [p["id"] for p in policy["policies"]]
        assert "SEC001" in policy_ids  # AWS key
        assert "SEC002" in policy_ids  # Private key

    def test_load_pack_pii(self):
        """load_pack('pii.v1') should return valid policy."""
        policy = load_pack("pii.v1")
        assert policy["schema_version"] == "1.0"
        assert "policies" in policy
        assert len(policy["policies"]) > 0

        # Check expected policy IDs
        policy_ids = [p["id"] for p in policy["policies"]]
        assert "PII001" in policy_ids  # Email
        assert "PII002" in policy_ids  # Phone
        assert "PII003" in policy_ids  # SSN
        assert "PII004" in policy_ids  # Credit card

    def test_load_pack_not_found(self):
        """load_pack with invalid name should raise PackError."""
        with pytest.raises(PackError) as exc_info:
            load_pack("nonexistent.pack")
        assert "not found" in str(exc_info.value).lower()

    def test_load_pack_shows_available(self):
        """PackError for not found should list available packs."""
        with pytest.raises(PackError) as exc_info:
            load_pack("nonexistent.pack")
        error_msg = str(exc_info.value)
        assert "secrets.v1" in error_msg or "pii.v1" in error_msg


class TestGetPackPath:
    """Tests for get_pack_path() function."""

    def test_get_pack_path_secrets(self):
        """get_pack_path should return valid path."""
        path = get_pack_path("secrets.v1")
        assert path.exists()
        assert path.suffix == ".json"

    def test_get_pack_path_not_found(self):
        """get_pack_path with invalid name should raise PackError."""
        with pytest.raises(PackError):
            get_pack_path("nonexistent.pack")


class TestPackNameValidation:
    """Tests for pack name validation (security)."""

    def test_valid_pack_names(self):
        """Valid pack names should pass validation."""
        valid_names = [
            "secrets.v1",
            "pii.v1",
            "custom-pack",
            "my_pack",
            "Pack123",
            "a",
            "a.b.c",
            "pack-v2.1",
        ]
        for name in valid_names:
            # Should not raise
            _validate_pack_name(name)

    def test_empty_pack_name(self):
        """Empty pack name should raise PackError."""
        with pytest.raises(PackError) as exc_info:
            _validate_pack_name("")
        assert "empty" in str(exc_info.value).lower()

    def test_path_traversal_dotdot(self):
        """Path traversal with .. should be rejected."""
        with pytest.raises(PackError) as exc_info:
            _validate_pack_name("../etc/passwd")
        assert "traversal" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()

    def test_path_traversal_slash(self):
        """Path traversal with / should be rejected."""
        with pytest.raises(PackError) as exc_info:
            _validate_pack_name("path/to/pack")
        assert "invalid" in str(exc_info.value).lower()

    def test_path_traversal_backslash(self):
        """Path traversal with \\ should be rejected."""
        with pytest.raises(PackError) as exc_info:
            _validate_pack_name("path\\to\\pack")
        assert "invalid" in str(exc_info.value).lower()

    def test_invalid_characters(self):
        """Invalid characters should be rejected."""
        invalid_names = [
            ".hidden",  # Starts with dot
            "-starts-with-dash",  # Starts with dash
            "_starts_with_underscore",  # Starts with underscore
            "has space",
            "has@symbol",
            "has$dollar",
        ]
        for name in invalid_names:
            with pytest.raises(PackError):
                _validate_pack_name(name)


class TestCLIListPacks:
    """Tests for CLI --list-packs."""

    def test_list_packs_exit_zero(self):
        """--list-packs should exit with 0."""
        result = run_cli("check", "--list-packs")
        assert result.returncode == 0

    def test_list_packs_shows_packs(self):
        """--list-packs should show available packs."""
        result = run_cli("check", "--list-packs")
        assert result.returncode == 0
        assert "secrets.v1" in result.stdout
        assert "pii.v1" in result.stdout

    def test_list_packs_deterministic(self):
        """--list-packs output should be deterministic."""
        result1 = run_cli("check", "--list-packs")
        result2 = run_cli("check", "--list-packs")
        assert result1.stdout == result2.stdout

    def test_list_packs_no_input_required(self):
        """--list-packs should work without --input."""
        result = run_cli("check", "--list-packs")
        assert result.returncode == 0


class TestCLIPolicyPackMutualExclusion:
    """Tests for CLI --policy XOR --pack enforcement."""

    def test_neither_policy_nor_pack(self):
        """check without --policy or --pack should fail with exit 2."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli("check", "--input", str(input_file))
        assert result.returncode == 2
        assert "must specify" in result.stderr.lower() or "required" in result.stderr.lower()

    def test_both_policy_and_pack(self):
        """check with both --policy and --pack should fail with exit 2."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"
        policy_file = fixtures / "policy_v1.json"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--policy", str(policy_file),
            "--pack", "secrets.v1",
        )
        assert result.returncode == 2
        # argparse uses "not allowed with argument" for mutually exclusive groups
        assert "not allowed with" in result.stderr.lower()

    def test_policy_only_works(self):
        """check with only --policy should work."""
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

    def test_pack_only_works(self):
        """check with only --pack should work."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )
        assert result.returncode == 0


class TestCLIPackExecution:
    """Tests for CLI check with --pack."""

    def test_pack_secrets_finds_violations(self):
        """--pack secrets.v1 should find secrets in sample input."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)

        assert output["format"] == "compliancepack.check.v1"
        assert output["policy_path"] == "pack:secrets.v1"

        # Should find AWS key and private key
        finding_ids = [f["id"] for f in output["findings"]]
        assert "SEC001" in finding_ids  # AWS key
        assert "SEC002" in finding_ids  # Private key

    def test_pack_pii_finds_violations(self):
        """--pack pii.v1 should find PII in sample input."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "pii.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)

        assert output["policy_path"] == "pack:pii.v1"

        # Should find email
        finding_ids = [f["id"] for f in output["findings"]]
        assert "PII001" in finding_ids  # Email

    def test_pack_invalid_name_fails(self):
        """--pack with invalid name should fail."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "nonexistent.pack",
        )
        assert result.returncode == 1
        assert "not found" in result.stderr.lower()

    def test_pack_path_traversal_fails(self):
        """--pack with path traversal should fail."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "../secrets.v1",
        )
        assert result.returncode == 1
        assert "invalid" in result.stderr.lower() or "traversal" in result.stderr.lower()


class TestPackDeterminism:
    """Tests for pack execution determinism."""

    def test_pack_output_deterministic(self):
        """Same command with --fixed-time should produce identical output."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        args = [
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        ]

        result1 = run_cli(*args)
        result2 = run_cli(*args)

        assert result1.returncode == 0
        assert result2.returncode == 0
        assert result1.stdout == result2.stdout

    def test_pack_output_schema_fields(self):
        """Pack output should have all required schema fields."""
        fixtures = Path(__file__).parent / "fixtures"
        input_file = fixtures / "sample_input.txt"

        result = run_cli(
            "check",
            "--input", str(input_file),
            "--pack", "secrets.v1",
            "--fixed-time", "2025-01-01T00:00:00Z",
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)

        # Required top-level fields
        assert output["format"] == "compliancepack.check.v1"
        assert output["generated_at_utc"] == "2025-01-01T00:00:00Z"
        assert "input_path" in output
        assert "policy_path" in output
        assert "redaction_applied" in output
        assert "summary" in output
        assert "findings" in output

        # Required summary fields
        summary = output["summary"]
        assert "policy_count" in summary
        assert "finding_count" in summary
        assert "severity_counts" in summary

        # Required severity counts
        severity_counts = summary["severity_counts"]
        assert "critical" in severity_counts
        assert "high" in severity_counts
        assert "medium" in severity_counts
        assert "low" in severity_counts
        assert "info" in severity_counts
