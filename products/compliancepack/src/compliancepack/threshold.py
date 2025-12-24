"""
CompliancePack Severity Threshold Enforcement.

Provides threshold comparison and violation counting for CI gate enforcement.

Severity ranking (lower = more severe):
- critical: 0
- high: 1
- medium: 2
- low: 3
- info: 4

Threshold semantics:
- A finding violates threshold if severity_rank <= threshold_rank
- Example: --fail-on high means critical and high both violate
"""

from typing import List, Tuple

from compliancepack.policy import SEVERITY_LEVELS, get_severity_rank


# Exit code semantics (must be deterministic)
EXIT_OK = 0           # No findings at/above threshold
EXIT_RUNTIME = 1      # Unexpected runtime error
EXIT_USAGE = 2        # CLI usage/config error
EXIT_VIOLATION = 3    # Findings at/above threshold exist


def get_threshold_rank(severity: str) -> int:
    """
    Get numeric rank for severity threshold.

    Args:
        severity: Severity level string

    Returns:
        Rank (0=critical, 1=high, 2=medium, 3=low, 4=info)

    Raises:
        ValueError: If severity is not valid
    """
    if severity not in SEVERITY_LEVELS:
        raise ValueError(
            f"Invalid severity '{severity}'. "
            f"Must be one of: {', '.join(SEVERITY_LEVELS)}"
        )
    return get_severity_rank(severity)


def severity_meets_threshold(finding_severity: str, threshold_severity: str) -> bool:
    """
    Check if a finding severity meets or exceeds the threshold.

    Args:
        finding_severity: Severity of the finding
        threshold_severity: Threshold severity level

    Returns:
        True if finding is at or above threshold (should fail CI)
    """
    finding_rank = get_severity_rank(finding_severity)
    threshold_rank = get_threshold_rank(threshold_severity)
    # Lower rank = more severe; finding violates if rank <= threshold
    return finding_rank <= threshold_rank


def count_violations(
    findings: List[dict],
    threshold_severity: str,
) -> Tuple[int, List[str]]:
    """
    Count findings that meet or exceed the threshold.

    Args:
        findings: List of finding dicts (must have 'severity' and 'id' keys)
        threshold_severity: Threshold severity level

    Returns:
        Tuple of (violation_count, list of violating finding IDs)
    """
    violations: List[str] = []
    for finding in findings:
        if severity_meets_threshold(finding["severity"], threshold_severity):
            violations.append(finding["id"])
    return len(violations), violations


def determine_exit_code(
    violation_count: int,
    exit_zero_override: bool = False,
) -> int:
    """
    Determine the appropriate exit code based on violations.

    Args:
        violation_count: Number of threshold violations
        exit_zero_override: If True, always return 0 (for --exit-zero)

    Returns:
        Exit code (0, 2, or 3)
    """
    if exit_zero_override:
        return EXIT_OK
    if violation_count > 0:
        return EXIT_VIOLATION
    return EXIT_OK
