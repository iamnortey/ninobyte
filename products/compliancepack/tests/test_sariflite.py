"""
CompliancePack SARIF-lite renderer tests.

Contract-grade tests for:
- Output schema structure
- Deterministic ordering
- Severity to level mapping
"""

import pytest

from compliancepack.sariflite import SEVERITY_TO_LEVEL, render_sariflite


def make_check_result(
    findings=None,
    input_path="test.txt",
    policy_path="pack:test.v1",
    generated_at_utc="2025-01-01T00:00:00Z",
    redaction_applied=True,
):
    """Create a minimal CheckResultDict for testing."""
    if findings is None:
        findings = []
    return {
        "format": "compliancepack.check.v1",
        "generated_at_utc": generated_at_utc,
        "input_path": input_path,
        "policy_path": policy_path,
        "redaction_applied": redaction_applied,
        "summary": {
            "policy_count": 3,
            "finding_count": len(findings),
            "severity_counts": {
                "critical": sum(1 for f in findings if f["severity"] == "critical"),
                "high": sum(1 for f in findings if f["severity"] == "high"),
                "medium": sum(1 for f in findings if f["severity"] == "medium"),
                "low": sum(1 for f in findings if f["severity"] == "low"),
                "info": sum(1 for f in findings if f["severity"] == "info"),
            },
        },
        "findings": findings,
    }


def make_finding(
    id="TEST001",
    title="Test Finding",
    severity="high",
    description="Test description",
    match_count=1,
    samples=None,
):
    """Create a minimal finding for testing."""
    if samples is None:
        samples = [{"line": 1, "col_start": 0, "col_end": 10, "excerpt": "test"}]
    return {
        "id": id,
        "title": title,
        "severity": severity,
        "description": description,
        "match_count": match_count,
        "samples": samples,
    }


class TestSeverityToLevelMapping:
    """Test severity to SARIF level mapping."""

    def test_critical_maps_to_error(self):
        """Critical severity maps to error level."""
        assert SEVERITY_TO_LEVEL["critical"] == "error"

    def test_high_maps_to_error(self):
        """High severity maps to error level."""
        assert SEVERITY_TO_LEVEL["high"] == "error"

    def test_medium_maps_to_warning(self):
        """Medium severity maps to warning level."""
        assert SEVERITY_TO_LEVEL["medium"] == "warning"

    def test_low_maps_to_note(self):
        """Low severity maps to note level."""
        assert SEVERITY_TO_LEVEL["low"] == "note"

    def test_info_maps_to_note(self):
        """Info severity maps to note level."""
        assert SEVERITY_TO_LEVEL["info"] == "note"


class TestSarifLiteSchema:
    """Test SARIF-lite output schema structure."""

    def test_format_is_sariflite(self):
        """Output format should be compliancepack.sariflite.v1."""
        result = make_check_result()
        output = render_sariflite(result)
        assert output["format"] == "compliancepack.sariflite.v1"

    def test_version_is_present(self):
        """Version field should be present."""
        result = make_check_result()
        output = render_sariflite(result)
        assert output["version"] == "sariflite.v1"

    def test_tool_structure(self):
        """Tool field should have correct structure."""
        result = make_check_result()
        output = render_sariflite(result)
        assert "tool" in output
        assert output["tool"]["name"] == "compliancepack"
        assert "version" in output["tool"]
        assert output["tool"]["rule_count"] == 3

    def test_runs_is_list_of_one(self):
        """Runs should be a list with one element."""
        result = make_check_result()
        output = render_sariflite(result)
        assert "runs" in output
        assert isinstance(output["runs"], list)
        assert len(output["runs"]) == 1

    def test_run_contains_required_fields(self):
        """Run should contain required fields."""
        result = make_check_result()
        output = render_sariflite(result)
        run = output["runs"][0]
        assert "input_path" in run
        assert "policy_path" in run
        assert "generated_at_utc" in run
        assert "redaction_applied" in run
        assert "results" in run

    def test_threshold_structure(self):
        """Threshold field should have correct structure."""
        result = make_check_result()
        output = render_sariflite(result, fail_on="medium", violation_count=2)
        assert "threshold" in output
        assert output["threshold"]["fail_on"] == "medium"
        assert output["threshold"]["violations"] == 2

    def test_summary_structure(self):
        """Summary field should have correct structure."""
        result = make_check_result()
        output = render_sariflite(result, exit_code_expected=3)
        assert "summary" in output
        assert "finding_count" in output["summary"]
        assert "severity_counts" in output["summary"]
        assert output["summary"]["exit_code_expected"] == 3
        assert "truncated" in output["summary"]


class TestSarifLiteResults:
    """Test SARIF-lite result transformation."""

    def test_empty_findings_empty_results(self):
        """No findings produces empty results."""
        result = make_check_result(findings=[])
        output = render_sariflite(result)
        assert output["runs"][0]["results"] == []

    def test_finding_to_result_mapping(self):
        """Finding should map to SARIF result correctly."""
        finding = make_finding(
            id="SEC001",
            title="AWS Key Found",
            severity="high",
            description="Found AWS key",
        )
        result = make_check_result(findings=[finding])
        output = render_sariflite(result)
        results = output["runs"][0]["results"]
        assert len(results) == 1
        r = results[0]
        assert r["ruleId"] == "SEC001"
        assert r["level"] == "error"
        assert r["message"] == "AWS Key Found"
        assert "locations" in r
        assert "properties" in r

    def test_result_properties(self):
        """Result properties should include expected fields."""
        finding = make_finding(severity="medium", description="Test desc")
        result = make_check_result(findings=[finding])
        output = render_sariflite(result)
        props = output["runs"][0]["results"][0]["properties"]
        assert props["severity"] == "medium"
        assert props["description"] == "Test desc"
        assert "match_count" in props
        assert "excerpt_redacted" in props

    def test_locations_from_samples(self):
        """Locations should be derived from samples."""
        samples = [
            {"line": 5, "col_start": 10, "col_end": 20, "excerpt": "test"},
            {"line": 10, "col_start": 0, "col_end": 5, "excerpt": "test2"},
        ]
        finding = make_finding(samples=samples)
        result = make_check_result(findings=[finding], input_path="config.txt")
        output = render_sariflite(result)
        locations = output["runs"][0]["results"][0]["locations"]
        assert len(locations) == 2
        assert locations[0]["file"] == "config.txt"
        assert locations[0]["line"] == 5
        assert locations[0]["col_start"] == 10


class TestSarifLiteDeterminism:
    """Test deterministic ordering of SARIF-lite output."""

    def test_results_sorted_by_level_then_ruleid(self):
        """Results should be sorted by level, then ruleId."""
        findings = [
            make_finding(id="Z001", severity="medium"),  # warning
            make_finding(id="A001", severity="high"),  # error
            make_finding(id="B001", severity="high"),  # error
        ]
        result = make_check_result(findings=findings)
        output = render_sariflite(result)
        results = output["runs"][0]["results"]
        # Errors first, then warnings; within errors, sorted by ruleId
        assert results[0]["ruleId"] == "A001"
        assert results[1]["ruleId"] == "B001"
        assert results[2]["ruleId"] == "Z001"

    def test_locations_sorted_by_line_then_col(self):
        """Locations within a result should be sorted."""
        samples = [
            {"line": 10, "col_start": 5, "col_end": 10, "excerpt": "b"},
            {"line": 5, "col_start": 0, "col_end": 5, "excerpt": "a"},
        ]
        finding = make_finding(samples=samples)
        result = make_check_result(findings=[finding])
        output = render_sariflite(result)
        locations = output["runs"][0]["results"][0]["locations"]
        assert locations[0]["line"] == 5
        assert locations[1]["line"] == 10


class TestSarifLiteTruncation:
    """Test truncation metadata."""

    def test_not_truncated_by_default(self):
        """Truncated should be False by default."""
        result = make_check_result()
        output = render_sariflite(result)
        assert output["summary"]["truncated"] is False

    def test_truncated_true_when_set(self):
        """Truncated should be True when specified."""
        result = make_check_result()
        output = render_sariflite(result, truncated=True)
        assert output["summary"]["truncated"] is True

    def test_max_findings_in_summary(self):
        """Max findings should appear in summary when set."""
        result = make_check_result()
        output = render_sariflite(result, max_findings=5)
        assert output["summary"]["max_findings"] == 5

    def test_max_findings_null_when_zero(self):
        """Max findings should be None when 0."""
        result = make_check_result()
        output = render_sariflite(result, max_findings=0)
        assert output["summary"]["max_findings"] is None
