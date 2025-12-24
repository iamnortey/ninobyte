"""
CompliancePack data models.

Defines the output schema for compliance check results.
"""

from typing import Any, Dict, List, Optional, TypedDict


class ViolationDict(TypedDict):
    """A single compliance violation."""
    rule_id: str
    severity: str  # "error", "warning", "info"
    message: str
    location: Optional[str]


class SummaryDict(TypedDict):
    """Summary statistics for a compliance check."""
    total_checks: int
    passed: int
    failed: int
    warnings: int


class CheckResultDict(TypedDict):
    """Complete compliance check result."""
    format: str
    version: str
    generated_at_utc: str
    input_file: str
    redacted: bool
    violations: List[ViolationDict]
    summary: SummaryDict


# Type alias for external use
CheckResult = CheckResultDict


def create_check_result(
    input_file: str,
    generated_at_utc: str,
    redact: bool = True,
    violations: Optional[List[ViolationDict]] = None,
) -> CheckResultDict:
    """
    Create a compliance check result.

    Args:
        input_file: Path to the analyzed file
        generated_at_utc: ISO8601 timestamp
        redact: Whether sensitive values were redacted
        violations: List of violations found (empty for scaffold)

    Returns:
        A CheckResultDict ready for JSON serialization
    """
    if violations is None:
        violations = []

    # Calculate summary
    failed = sum(1 for v in violations if v.get("severity") == "error")
    warnings = sum(1 for v in violations if v.get("severity") == "warning")
    passed = len(violations) == 0  # Scaffold: no checks = passed

    return {
        "format": "compliance-check",
        "version": "1.0.0",
        "generated_at_utc": generated_at_utc,
        "input_file": input_file,
        "redacted": redact,
        "violations": violations,
        "summary": {
            "total_checks": 0,  # Scaffold: no actual checks yet
            "passed": 0 if failed > 0 else 1,
            "failed": failed,
            "warnings": warnings,
        },
    }
