"""
CompliancePack threshold enforcement tests.

Contract-grade tests for:
- Severity ranking and comparison
- Threshold violation counting
- Exit code determination
"""

import pytest

from compliancepack.threshold import (
    EXIT_OK,
    EXIT_RUNTIME,
    EXIT_USAGE,
    EXIT_VIOLATION,
    count_violations,
    determine_exit_code,
    get_threshold_rank,
    severity_meets_threshold,
)


class TestExitCodes:
    """Verify exit code constants."""

    def test_exit_ok_is_zero(self):
        """EXIT_OK should be 0."""
        assert EXIT_OK == 0

    def test_exit_runtime_is_one(self):
        """EXIT_RUNTIME should be 1."""
        assert EXIT_RUNTIME == 1

    def test_exit_usage_is_two(self):
        """EXIT_USAGE should be 2."""
        assert EXIT_USAGE == 2

    def test_exit_violation_is_three(self):
        """EXIT_VIOLATION should be 3."""
        assert EXIT_VIOLATION == 3


class TestSeverityRanking:
    """Test severity ranking functions."""

    def test_critical_is_rank_zero(self):
        """Critical severity should have rank 0 (most severe)."""
        assert get_threshold_rank("critical") == 0

    def test_high_is_rank_one(self):
        """High severity should have rank 1."""
        assert get_threshold_rank("high") == 1

    def test_medium_is_rank_two(self):
        """Medium severity should have rank 2."""
        assert get_threshold_rank("medium") == 2

    def test_low_is_rank_three(self):
        """Low severity should have rank 3."""
        assert get_threshold_rank("low") == 3

    def test_info_is_rank_four(self):
        """Info severity should have rank 4 (least severe)."""
        assert get_threshold_rank("info") == 4

    def test_invalid_severity_raises(self):
        """Invalid severity should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_threshold_rank("unknown")
        assert "Invalid severity" in str(exc_info.value)


class TestSeverityMeetsThreshold:
    """Test threshold comparison logic."""

    def test_critical_meets_critical_threshold(self):
        """Critical finding meets critical threshold."""
        assert severity_meets_threshold("critical", "critical") is True

    def test_critical_meets_high_threshold(self):
        """Critical finding meets high threshold."""
        assert severity_meets_threshold("critical", "high") is True

    def test_critical_meets_info_threshold(self):
        """Critical finding meets info threshold."""
        assert severity_meets_threshold("critical", "info") is True

    def test_high_meets_high_threshold(self):
        """High finding meets high threshold."""
        assert severity_meets_threshold("high", "high") is True

    def test_high_does_not_meet_critical_threshold(self):
        """High finding does not meet critical-only threshold."""
        assert severity_meets_threshold("high", "critical") is False

    def test_medium_meets_medium_threshold(self):
        """Medium finding meets medium threshold."""
        assert severity_meets_threshold("medium", "medium") is True

    def test_medium_does_not_meet_high_threshold(self):
        """Medium finding does not meet high threshold."""
        assert severity_meets_threshold("medium", "high") is False

    def test_low_meets_low_threshold(self):
        """Low finding meets low threshold."""
        assert severity_meets_threshold("low", "low") is True

    def test_low_does_not_meet_medium_threshold(self):
        """Low finding does not meet medium threshold."""
        assert severity_meets_threshold("low", "medium") is False

    def test_info_meets_info_threshold(self):
        """Info finding meets info threshold."""
        assert severity_meets_threshold("info", "info") is True

    def test_info_does_not_meet_low_threshold(self):
        """Info finding does not meet low threshold."""
        assert severity_meets_threshold("info", "low") is False


class TestCountViolations:
    """Test violation counting."""

    def test_empty_findings_zero_violations(self):
        """Empty findings list has zero violations."""
        count, ids = count_violations([], "high")
        assert count == 0
        assert ids == []

    def test_all_below_threshold(self):
        """Findings all below threshold have zero violations."""
        findings = [
            {"id": "TEST001", "severity": "low"},
            {"id": "TEST002", "severity": "info"},
        ]
        count, ids = count_violations(findings, "high")
        assert count == 0
        assert ids == []

    def test_all_at_or_above_threshold(self):
        """All findings at/above threshold count as violations."""
        findings = [
            {"id": "TEST001", "severity": "critical"},
            {"id": "TEST002", "severity": "high"},
        ]
        count, ids = count_violations(findings, "high")
        assert count == 2
        assert ids == ["TEST001", "TEST002"]

    def test_mixed_severities(self):
        """Mixed severities count correctly."""
        findings = [
            {"id": "TEST001", "severity": "critical"},
            {"id": "TEST002", "severity": "medium"},
            {"id": "TEST003", "severity": "low"},
        ]
        count, ids = count_violations(findings, "medium")
        assert count == 2
        assert "TEST001" in ids
        assert "TEST002" in ids
        assert "TEST003" not in ids

    def test_info_threshold_catches_all(self):
        """Info threshold catches all findings."""
        findings = [
            {"id": "TEST001", "severity": "critical"},
            {"id": "TEST002", "severity": "info"},
        ]
        count, ids = count_violations(findings, "info")
        assert count == 2


class TestDetermineExitCode:
    """Test exit code determination."""

    def test_zero_violations_exit_ok(self):
        """Zero violations returns EXIT_OK."""
        assert determine_exit_code(0) == EXIT_OK

    def test_one_violation_exit_violation(self):
        """One violation returns EXIT_VIOLATION."""
        assert determine_exit_code(1) == EXIT_VIOLATION

    def test_many_violations_exit_violation(self):
        """Many violations returns EXIT_VIOLATION."""
        assert determine_exit_code(100) == EXIT_VIOLATION

    def test_exit_zero_override_with_violations(self):
        """Exit zero override forces EXIT_OK even with violations."""
        assert determine_exit_code(5, exit_zero_override=True) == EXIT_OK

    def test_exit_zero_override_without_violations(self):
        """Exit zero override with no violations still returns EXIT_OK."""
        assert determine_exit_code(0, exit_zero_override=True) == EXIT_OK
