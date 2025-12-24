"""
CompliancePack Matcher Engine Tests.

Tests for regex and contains matching with deterministic ordering.
"""

import json
from pathlib import Path

import pytest

from compliancepack.engine import apply_policy, run_check
from compliancepack.policy import load_policy_file


class TestApplyPolicy:
    """Tests for apply_policy function."""

    def test_regex_match(self):
        """Regex pattern should find matches."""
        lines = ["This is a test line", "Another test here", "No match here"]
        policy = {
            "id": "CP0001",
            "title": "Test Pattern",
            "severity": "high",
            "type": "regex",
            "pattern": "test",
            "needle": None,
            "description": "Find test",
            "sample_limit": 10,
        }

        result = apply_policy(lines, policy, apply_redaction=False)

        assert result is not None
        assert result["id"] == "CP0001"
        assert result["match_count"] == 2
        assert len(result["samples"]) == 2

    def test_contains_match(self):
        """Contains should find substring matches."""
        lines = ["Hello world", "World of warcraft", "No match"]
        policy = {
            "id": "CP0001",
            "title": "World Pattern",
            "severity": "medium",
            "type": "contains",
            "pattern": None,
            "needle": "world",
            "description": "Find world",
            "sample_limit": 10,
        }

        result = apply_policy(lines, policy, apply_redaction=False)

        assert result is not None
        assert result["match_count"] == 1  # Case sensitive: only lowercase "world"

    def test_no_matches_returns_none(self):
        """No matches should return None."""
        lines = ["This is a test", "Another line"]
        policy = {
            "id": "CP0001",
            "title": "No Match",
            "severity": "high",
            "type": "contains",
            "pattern": None,
            "needle": "xyz123",
            "description": "Won't match",
            "sample_limit": 10,
        }

        result = apply_policy(lines, policy, apply_redaction=False)

        assert result is None

    def test_sample_limit(self):
        """sample_limit should cap the number of samples."""
        lines = ["match match match match match"]
        policy = {
            "id": "CP0001",
            "title": "Many Matches",
            "severity": "high",
            "type": "contains",
            "pattern": None,
            "needle": "match",
            "description": "Find all matches",
            "sample_limit": 2,
        }

        result = apply_policy(lines, policy, apply_redaction=False)

        assert result is not None
        assert result["match_count"] == 5  # Total matches
        assert len(result["samples"]) == 2  # But only 2 samples

    def test_matches_sorted_by_line_then_col(self):
        """Matches should be sorted by line, then col_start."""
        lines = ["b match a match", "a match first"]
        policy = {
            "id": "CP0001",
            "title": "Order Test",
            "severity": "high",
            "type": "contains",
            "pattern": None,
            "needle": "match",
            "description": "Test ordering",
            "sample_limit": 10,
        }

        result = apply_policy(lines, policy, apply_redaction=False)

        assert result is not None
        samples = result["samples"]
        # Should be sorted: line 1 col 2, line 1 col 10, line 2 col 2
        assert samples[0]["line"] == 1
        assert samples[0]["col_start"] == 2
        assert samples[1]["line"] == 1
        assert samples[1]["col_start"] == 10
        assert samples[2]["line"] == 2

    def test_line_numbers_1_indexed(self):
        """Line numbers should be 1-indexed."""
        lines = ["first line", "second line with match"]
        policy = {
            "id": "CP0001",
            "title": "Line Index Test",
            "severity": "high",
            "type": "contains",
            "pattern": None,
            "needle": "match",
            "description": "Test line indexing",
            "sample_limit": 10,
        }

        result = apply_policy(lines, policy, apply_redaction=False)

        assert result is not None
        assert result["samples"][0]["line"] == 2  # 1-indexed


class TestRunCheck:
    """Tests for run_check function."""

    def test_run_check_with_fixtures(self, tmp_path: Path):
        """run_check should work with policy and input files."""
        # Create input file
        input_file = tmp_path / "input.txt"
        input_file.write_text("This contains a secret: AKIAIOSFODNN7EXAMPLE\n")

        # Create policy file
        policy = {
            "schema_version": "1.0",
            "policies": [
                {
                    "id": "CP0001",
                    "title": "AWS Key",
                    "severity": "high",
                    "type": "regex",
                    "pattern": "AKIA[0-9A-Z]{16}",
                    "description": "Find AWS keys",
                    "sample_limit": 3,
                }
            ],
        }
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy))

        # Load policy and run check
        policy_data = load_policy_file(policy_file)
        result = run_check(
            input_path=str(input_file),
            policy_file=policy_data,
            policy_path=str(policy_file),
            generated_at_utc="2025-01-01T00:00:00Z",
            apply_redaction=True,
        )

        assert result["format"] == "compliancepack.check.v1"
        assert result["generated_at_utc"] == "2025-01-01T00:00:00Z"
        assert result["summary"]["finding_count"] == 1
        assert result["redaction_applied"] is True

    def test_findings_sorted_by_severity_then_id(self, tmp_path: Path):
        """Findings should be sorted by severity (most severe first), then by id."""
        # Create input file with multiple matches
        input_file = tmp_path / "input.txt"
        input_file.write_text("low medium high critical\n")

        # Create policy with different severities (out of order)
        policy = {
            "schema_version": "1.0",
            "policies": [
                {
                    "id": "CP0003",
                    "title": "Low",
                    "severity": "low",
                    "type": "contains",
                    "needle": "low",
                    "description": "Low severity",
                },
                {
                    "id": "CP0001",
                    "title": "Critical",
                    "severity": "critical",
                    "type": "contains",
                    "needle": "critical",
                    "description": "Critical severity",
                },
                {
                    "id": "CP0002",
                    "title": "High",
                    "severity": "high",
                    "type": "contains",
                    "needle": "high",
                    "description": "High severity",
                },
            ],
        }
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy))

        policy_data = load_policy_file(policy_file)
        result = run_check(
            input_path=str(input_file),
            policy_file=policy_data,
            policy_path=str(policy_file),
            generated_at_utc="2025-01-01T00:00:00Z",
            apply_redaction=False,
        )

        findings = result["findings"]
        severities = [f["severity"] for f in findings]
        # Should be: critical, high, low (sorted by severity rank)
        assert severities == ["critical", "high", "low"]

    def test_severity_counts(self, tmp_path: Path):
        """Summary should include correct severity counts."""
        input_file = tmp_path / "input.txt"
        input_file.write_text("a b c\n")

        policy = {
            "schema_version": "1.0",
            "policies": [
                {
                    "id": "CP0001",
                    "title": "A",
                    "severity": "critical",
                    "type": "contains",
                    "needle": "a",
                    "description": "A",
                },
                {
                    "id": "CP0002",
                    "title": "B",
                    "severity": "high",
                    "type": "contains",
                    "needle": "b",
                    "description": "B",
                },
                {
                    "id": "CP0003",
                    "title": "C",
                    "severity": "high",
                    "type": "contains",
                    "needle": "c",
                    "description": "C",
                },
            ],
        }
        policy_file = tmp_path / "policy.json"
        policy_file.write_text(json.dumps(policy))

        policy_data = load_policy_file(policy_file)
        result = run_check(
            input_path=str(input_file),
            policy_file=policy_data,
            policy_path=str(policy_file),
            generated_at_utc="2025-01-01T00:00:00Z",
            apply_redaction=False,
        )

        counts = result["summary"]["severity_counts"]
        assert counts["critical"] == 1
        assert counts["high"] == 2
        assert counts["medium"] == 0
        assert counts["low"] == 0
        assert counts["info"] == 0
