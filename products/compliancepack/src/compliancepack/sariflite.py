"""
CompliancePack SARIF-Lite Renderer.

Produces a SARIF-adjacent JSON format that is:
- Deterministic (stable ordering, sort_keys=True)
- Stdlib-only (no external dependencies)
- CI-friendly (structured for easy parsing)

Format: compliancepack.sariflite.v1

Mapping from CompliancePack severity to SARIF level:
- critical -> error
- high -> error
- medium -> warning
- low -> note
- info -> note
"""

from typing import Any, Dict, List, TypedDict

from compliancepack.engine import CheckResultDict, FindingDict, MatchDict


# SARIF level mapping
SEVERITY_TO_LEVEL: Dict[str, str] = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
    "info": "note",
}


class SarifLocation(TypedDict):
    """A SARIF-lite location."""
    file: str
    line: int
    col_start: int
    col_end: int


class SarifResult(TypedDict):
    """A SARIF-lite result (finding)."""
    ruleId: str
    level: str
    message: str
    locations: List[SarifLocation]
    properties: Dict[str, Any]


class SarifRun(TypedDict):
    """A SARIF-lite run."""
    input_path: str
    policy_path: str
    generated_at_utc: str
    redaction_applied: bool
    results: List[SarifResult]


class SarifTool(TypedDict):
    """SARIF-lite tool info."""
    name: str
    version: str
    rule_count: int


class SarifLiteReport(TypedDict):
    """Complete SARIF-lite report."""
    format: str
    version: str
    tool: SarifTool
    runs: List[SarifRun]
    threshold: Dict[str, Any]
    summary: Dict[str, Any]


def _finding_to_result(
    finding: FindingDict,
    default_input_path: str,
) -> SarifResult:
    """
    Convert a CompliancePack finding to a SARIF-lite result.

    Args:
        finding: CompliancePack finding dict
        default_input_path: Default path for locations (single-file mode)

    Returns:
        SARIF-lite result dict
    """
    # Build locations from samples
    locations: List[SarifLocation] = []
    for sample in finding["samples"]:
        # Multi-file mode: samples have "file" field
        # Single-file mode: use default_input_path
        file_path = sample.get("file", default_input_path)
        locations.append({
            "file": file_path,
            "line": sample["line"],
            "col_start": sample["col_start"],
            "col_end": sample["col_end"],
        })

    # Sort locations for determinism (by file, then line, then col)
    locations.sort(key=lambda loc: (loc["file"], loc["line"], loc["col_start"]))

    return {
        "ruleId": finding["id"],
        "level": SEVERITY_TO_LEVEL.get(finding["severity"], "note"),
        "message": finding["title"],
        "locations": locations,
        "properties": {
            "severity": finding["severity"],
            "description": finding["description"],
            "match_count": finding["match_count"],
            "excerpt_redacted": any(
                "[REDACTED" in sample.get("excerpt", "")
                for sample in finding["samples"]
            ),
        },
    }


def render_sariflite(
    report: CheckResultDict,
    fail_on: str = "high",
    violation_count: int = 0,
    exit_code_expected: int = 0,
    max_findings: int = 0,
    truncated: bool = False,
) -> SarifLiteReport:
    """
    Render a CheckResultDict as SARIF-lite format.

    Pure function with no IO side effects.

    Args:
        report: CheckResultDict from run_check()
        fail_on: Threshold severity level
        violation_count: Number of threshold violations
        exit_code_expected: Expected exit code
        max_findings: Maximum findings limit (0 = unlimited)
        truncated: Whether findings were truncated

    Returns:
        SARIF-lite report dict ready for JSON serialization
    """
    # Determine input path (single-file) or inputs (multi-file)
    # Multi-file mode uses "inputs" array, single-file uses "input_path"
    if "inputs" in report:
        # Multi-file mode
        input_path = ",".join(sorted(report["inputs"]))
        default_file_path = report["inputs"][0] if report["inputs"] else ""
    else:
        # Single-file mode
        input_path = report["input_path"]
        default_file_path = input_path

    # Convert findings to results
    results: List[SarifResult] = []
    for finding in report["findings"]:
        results.append(_finding_to_result(finding, default_file_path))

    # Sort results by (level, ruleId, first location) for determinism
    def result_sort_key(r: SarifResult) -> tuple:
        # level ordering: error < warning < note
        level_order = {"error": 0, "warning": 1, "note": 2}
        first_loc = r["locations"][0] if r["locations"] else {"file": "", "line": 0, "col_start": 0}
        return (
            level_order.get(r["level"], 3),
            r["ruleId"],
            first_loc.get("file", ""),
            first_loc["line"],
            first_loc["col_start"],
        )

    results.sort(key=result_sort_key)

    return {
        "format": "compliancepack.sariflite.v1",
        "version": "sariflite.v1",
        "tool": {
            "name": "compliancepack",
            "version": "0.10.0",
            "rule_count": report["summary"]["policy_count"],
        },
        "runs": [
            {
                "input_path": input_path,
                "policy_path": report["policy_path"],
                "generated_at_utc": report["generated_at_utc"],
                "redaction_applied": report["redaction_applied"],
                "results": results,
            }
        ],
        "threshold": {
            "fail_on": fail_on,
            "violations": violation_count,
        },
        "summary": {
            "finding_count": report["summary"]["finding_count"],
            "severity_counts": report["summary"]["severity_counts"],
            "exit_code_expected": exit_code_expected,
            "truncated": truncated,
            "max_findings": max_findings if max_findings > 0 else None,
        },
    }
