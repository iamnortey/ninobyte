"""
Incident Triage Tests

Tests for the incident-triage command and triage_incident function.
Uses golden file comparisons to ensure deterministic output.
"""

import json
from pathlib import Path

import pytest

# Path setup is handled by conftest.py
from ninobyte_opspack.triage import triage_incident, TRIAGE_SCHEMA_VERSION
from ninobyte_opspack.version import __version__


# Find repo root and set up paths
def find_repo_root() -> Path:
    """Find repository root by walking up from this file until .git is found."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
    return Path(__file__).resolve().parent.parent.parent.parent


REPO_ROOT = find_repo_root()
OPSPACK_ROOT = REPO_ROOT / "products" / "opspack"
FIXTURES_DIR = OPSPACK_ROOT / "tests" / "fixtures"
GOLDENS_DIR = OPSPACK_ROOT / "tests" / "goldens"


class TestTriageIncidentFunction:
    """Tests for the triage_incident function."""

    def test_returns_required_schema_fields(self):
        """Triage result must contain all required top-level fields."""
        incident = {
            "id": "TEST-001",
            "title": "Test incident",
            "description": "This is a test"
        }
        result = triage_incident(incident)

        required_fields = [
            "version",
            "opspack_version",
            "incident",
            "classification",
            "recommended_actions",
            "risk_flags",
            "evidence"
        ]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

    def test_classification_has_severity_and_category(self):
        """Classification must contain severity and category."""
        incident = {"id": "TEST-001", "title": "Test"}
        result = triage_incident(incident)

        assert "severity" in result["classification"]
        assert "category" in result["classification"]

    def test_severity_values_are_valid(self):
        """Severity must be one of the valid values."""
        valid_severities = ["critical", "high", "medium", "low"]

        incident = {"id": "TEST-001", "title": "Test"}
        result = triage_incident(incident)

        assert result["classification"]["severity"] in valid_severities

    def test_deterministic_output(self):
        """Same input must produce same output."""
        incident = {
            "id": "TEST-001",
            "title": "Database connection timeout",
            "description": "The database is slow",
            "affected_services": ["api", "web"],
            "users_affected": 100
        }

        result1 = triage_incident(incident)
        result2 = triage_incident(incident)

        # Compare as JSON strings for exact equality
        json1 = json.dumps(result1, sort_keys=True)
        json2 = json.dumps(result2, sort_keys=True)

        assert json1 == json2, "Output is not deterministic"

    def test_version_fields(self):
        """Version fields must match expected values."""
        incident = {"id": "TEST-001", "title": "Test"}
        result = triage_incident(incident)

        assert result["version"] == TRIAGE_SCHEMA_VERSION
        assert result["opspack_version"] == __version__


class TestSecurityBreach:
    """Golden test for security breach incident."""

    def test_security_breach_golden(self):
        """Security breach incident must produce expected golden output."""
        fixture_path = FIXTURES_DIR / "incident_security_breach.json"
        golden_path = GOLDENS_DIR / "incident_security_breach_expected.json"

        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
        assert golden_path.exists(), f"Golden not found: {golden_path}"

        # Load fixture
        with open(fixture_path, "r", encoding="utf-8") as f:
            incident = json.load(f)

        # Load expected golden
        with open(golden_path, "r", encoding="utf-8") as f:
            expected = json.load(f)

        # Run triage
        result = triage_incident(incident)

        # Compare as sorted JSON for deterministic comparison
        result_json = json.dumps(result, sort_keys=True)
        expected_json = json.dumps(expected, sort_keys=True)

        assert result_json == expected_json, (
            f"Golden mismatch for security breach incident.\n"
            f"Expected:\n{expected_json}\n"
            f"Got:\n{result_json}"
        )

    def test_security_breach_classification(self):
        """Security breach must be classified as critical security incident."""
        fixture_path = FIXTURES_DIR / "incident_security_breach.json"

        with open(fixture_path, "r", encoding="utf-8") as f:
            incident = json.load(f)

        result = triage_incident(incident)

        assert result["classification"]["severity"] == "critical"
        assert result["classification"]["category"] == "security"

    def test_security_breach_has_security_flag(self):
        """Security breach must have SECURITY_INCIDENT risk flag."""
        fixture_path = FIXTURES_DIR / "incident_security_breach.json"

        with open(fixture_path, "r", encoding="utf-8") as f:
            incident = json.load(f)

        result = triage_incident(incident)

        flags = [f["flag"] for f in result["risk_flags"]]
        assert "SECURITY_INCIDENT" in flags


class TestServiceDegradation:
    """Golden test for service degradation incident."""

    def test_service_degradation_golden(self):
        """Service degradation incident must produce expected golden output."""
        fixture_path = FIXTURES_DIR / "incident_service_degradation.json"
        golden_path = GOLDENS_DIR / "incident_service_degradation_expected.json"

        assert fixture_path.exists(), f"Fixture not found: {fixture_path}"
        assert golden_path.exists(), f"Golden not found: {golden_path}"

        # Load fixture
        with open(fixture_path, "r", encoding="utf-8") as f:
            incident = json.load(f)

        # Load expected golden
        with open(golden_path, "r", encoding="utf-8") as f:
            expected = json.load(f)

        # Run triage
        result = triage_incident(incident)

        # Compare as sorted JSON for deterministic comparison
        result_json = json.dumps(result, sort_keys=True)
        expected_json = json.dumps(expected, sort_keys=True)

        assert result_json == expected_json, (
            f"Golden mismatch for service degradation incident.\n"
            f"Expected:\n{expected_json}\n"
            f"Got:\n{result_json}"
        )

    def test_service_degradation_classification(self):
        """Service degradation with timeout keywords must be classified as high performance."""
        fixture_path = FIXTURES_DIR / "incident_service_degradation.json"

        with open(fixture_path, "r", encoding="utf-8") as f:
            incident = json.load(f)

        result = triage_incident(incident)

        assert result["classification"]["category"] == "performance"
        # High severity due to timeout keyword and user impact
        assert result["classification"]["severity"] == "high"


class TestCLIModule:
    """Tests for CLI module structure."""

    def test_cli_module_exists(self):
        """CLI module must exist."""
        cli_path = OPSPACK_ROOT / "src" / "ninobyte_opspack" / "cli.py"
        assert cli_path.exists(), "CLI module not found"

    def test_main_module_exists(self):
        """__main__.py must exist for module-style invocation."""
        main_path = OPSPACK_ROOT / "src" / "ninobyte_opspack" / "__main__.py"
        assert main_path.exists(), "__main__.py not found"

    def test_cli_can_be_imported(self):
        """CLI module must be importable."""
        from ninobyte_opspack.cli import main, create_parser
        assert callable(main)
        assert callable(create_parser)


class TestReadOnlyPosture:
    """Verify triage module maintains read-only posture."""

    def test_no_forbidden_imports(self):
        """Triage module must not import forbidden modules."""
        triage_path = OPSPACK_ROOT / "src" / "ninobyte_opspack" / "triage.py"
        content = triage_path.read_text(encoding="utf-8")

        forbidden = ["socket", "subprocess", "requests", "httpx", "urllib", "aiohttp", "paramiko"]
        for module in forbidden:
            assert f"import {module}" not in content, f"Forbidden import: {module}"
            assert f"from {module}" not in content, f"Forbidden import: from {module}"

    def test_cli_no_forbidden_imports(self):
        """CLI module must not import forbidden modules."""
        cli_path = OPSPACK_ROOT / "src" / "ninobyte_opspack" / "cli.py"
        content = cli_path.read_text(encoding="utf-8")

        forbidden = ["socket", "subprocess", "requests", "httpx", "urllib", "aiohttp", "paramiko"]
        for module in forbidden:
            assert f"import {module}" not in content, f"Forbidden import: {module}"
            assert f"from {module}" not in content, f"Forbidden import: from {module}"
