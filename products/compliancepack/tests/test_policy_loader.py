"""
CompliancePack Policy Loader Tests.

Tests for policy schema validation and deterministic ordering.
"""

import json
import tempfile
from pathlib import Path

import pytest

from compliancepack.policy import (
    PolicyValidationError,
    get_severity_rank,
    load_policy_file,
)


class TestLoadPolicyFile:
    """Tests for load_policy_file function."""

    def test_load_valid_policy(self, tmp_path: Path):
        """Valid policy file should load successfully."""
        policy = {
            "schema_version": "1.0",
            "policies": [
                {
                    "id": "CP0001",
                    "title": "Test Policy",
                    "severity": "high",
                    "type": "regex",
                    "pattern": "test.*",
                    "description": "Test description",
                    "sample_limit": 3,
                }
            ],
        }
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy))

        result = load_policy_file(policy_file)

        assert result["schema_version"] == "1.0"
        assert len(result["policies"]) == 1
        assert result["policies"][0]["id"] == "CP0001"

    def test_policies_sorted_by_id(self, tmp_path: Path):
        """Policies should be sorted by id for deterministic ordering."""
        policy = {
            "schema_version": "1.0",
            "policies": [
                {
                    "id": "CP0003",
                    "title": "Third",
                    "severity": "low",
                    "type": "contains",
                    "needle": "c",
                    "description": "Third policy",
                },
                {
                    "id": "CP0001",
                    "title": "First",
                    "severity": "high",
                    "type": "contains",
                    "needle": "a",
                    "description": "First policy",
                },
                {
                    "id": "CP0002",
                    "title": "Second",
                    "severity": "medium",
                    "type": "contains",
                    "needle": "b",
                    "description": "Second policy",
                },
            ],
        }
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy))

        result = load_policy_file(policy_file)

        ids = [p["id"] for p in result["policies"]]
        assert ids == ["CP0001", "CP0002", "CP0003"]

    def test_missing_schema_version(self, tmp_path: Path):
        """Missing schema_version should raise error."""
        policy = {"policies": []}
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy))

        with pytest.raises(PolicyValidationError, match="schema_version"):
            load_policy_file(policy_file)

    def test_unsupported_schema_version(self, tmp_path: Path):
        """Unsupported schema version should raise error."""
        policy = {"schema_version": "2.0", "policies": []}
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy))

        with pytest.raises(PolicyValidationError, match="Unsupported schema version"):
            load_policy_file(policy_file)

    def test_missing_policies(self, tmp_path: Path):
        """Missing policies array should raise error."""
        policy = {"schema_version": "1.0"}
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy))

        with pytest.raises(PolicyValidationError, match="policies"):
            load_policy_file(policy_file)

    def test_file_not_found(self, tmp_path: Path):
        """Non-existent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_policy_file(tmp_path / "nonexistent.json")

    def test_invalid_json(self, tmp_path: Path):
        """Invalid JSON should raise JSONDecodeError."""
        policy_file = tmp_path / "policy.json"
        policy_file.write_text("not valid json")

        with pytest.raises(json.JSONDecodeError):
            load_policy_file(policy_file)


class TestPolicyValidation:
    """Tests for individual policy validation."""

    def test_missing_required_field(self, tmp_path: Path):
        """Missing required field should raise error."""
        policy = {
            "schema_version": "1.0",
            "policies": [
                {
                    "id": "CP0001",
                    # missing title
                    "severity": "high",
                    "type": "regex",
                    "pattern": "test",
                    "description": "Test",
                }
            ],
        }
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy))

        with pytest.raises(PolicyValidationError, match="title"):
            load_policy_file(policy_file)

    def test_invalid_severity(self, tmp_path: Path):
        """Invalid severity should raise error."""
        policy = {
            "schema_version": "1.0",
            "policies": [
                {
                    "id": "CP0001",
                    "title": "Test",
                    "severity": "invalid",
                    "type": "regex",
                    "pattern": "test",
                    "description": "Test",
                }
            ],
        }
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy))

        with pytest.raises(PolicyValidationError, match="invalid severity"):
            load_policy_file(policy_file)

    def test_invalid_type(self, tmp_path: Path):
        """Invalid type should raise error."""
        policy = {
            "schema_version": "1.0",
            "policies": [
                {
                    "id": "CP0001",
                    "title": "Test",
                    "severity": "high",
                    "type": "unknown",
                    "description": "Test",
                }
            ],
        }
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy))

        with pytest.raises(PolicyValidationError, match="invalid type"):
            load_policy_file(policy_file)

    def test_regex_missing_pattern(self, tmp_path: Path):
        """Regex type without pattern should raise error."""
        policy = {
            "schema_version": "1.0",
            "policies": [
                {
                    "id": "CP0001",
                    "title": "Test",
                    "severity": "high",
                    "type": "regex",
                    "description": "Test",
                }
            ],
        }
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy))

        with pytest.raises(PolicyValidationError, match="pattern"):
            load_policy_file(policy_file)

    def test_contains_missing_needle(self, tmp_path: Path):
        """Contains type without needle should raise error."""
        policy = {
            "schema_version": "1.0",
            "policies": [
                {
                    "id": "CP0001",
                    "title": "Test",
                    "severity": "high",
                    "type": "contains",
                    "description": "Test",
                }
            ],
        }
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy))

        with pytest.raises(PolicyValidationError, match="needle"):
            load_policy_file(policy_file)

    def test_invalid_regex_pattern(self, tmp_path: Path):
        """Invalid regex pattern should raise error."""
        policy = {
            "schema_version": "1.0",
            "policies": [
                {
                    "id": "CP0001",
                    "title": "Test",
                    "severity": "high",
                    "type": "regex",
                    "pattern": "[invalid(",
                    "description": "Test",
                }
            ],
        }
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy))

        with pytest.raises(PolicyValidationError, match="invalid regex"):
            load_policy_file(policy_file)

    def test_duplicate_policy_ids(self, tmp_path: Path):
        """Duplicate policy ids should raise error."""
        policy = {
            "schema_version": "1.0",
            "policies": [
                {
                    "id": "CP0001",
                    "title": "First",
                    "severity": "high",
                    "type": "contains",
                    "needle": "a",
                    "description": "First",
                },
                {
                    "id": "CP0001",
                    "title": "Duplicate",
                    "severity": "low",
                    "type": "contains",
                    "needle": "b",
                    "description": "Duplicate",
                },
            ],
        }
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy))

        with pytest.raises(PolicyValidationError, match="Duplicate"):
            load_policy_file(policy_file)

    def test_default_sample_limit(self, tmp_path: Path):
        """sample_limit should default to 3 if not specified."""
        policy = {
            "schema_version": "1.0",
            "policies": [
                {
                    "id": "CP0001",
                    "title": "Test",
                    "severity": "high",
                    "type": "contains",
                    "needle": "test",
                    "description": "Test",
                }
            ],
        }
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy))

        result = load_policy_file(policy_file)

        assert result["policies"][0]["sample_limit"] == 3


class TestSeverityRank:
    """Tests for severity ranking."""

    def test_severity_order(self):
        """Severity ranks should be in correct order."""
        assert get_severity_rank("critical") < get_severity_rank("high")
        assert get_severity_rank("high") < get_severity_rank("medium")
        assert get_severity_rank("medium") < get_severity_rank("low")
        assert get_severity_rank("low") < get_severity_rank("info")

    def test_unknown_severity(self):
        """Unknown severity should return high value."""
        assert get_severity_rank("unknown") == 999
