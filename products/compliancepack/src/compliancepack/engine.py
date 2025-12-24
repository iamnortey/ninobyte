"""
CompliancePack Matcher Engine.

Applies policies to input text with deterministic matching and ordering.

Matching semantics:
- Read input as lines with stable line numbers (1-indexed)
- For regex: re.finditer per line
- For contains: find substring occurrences per line
- Store matches with line, col_start, col_end, excerpt

Deterministic ordering:
- Findings sorted by: severity rank (asc = more severe first), then policy id
- Matches sorted by: line asc, col_start asc
- Samples capped by sample_limit, taking earliest matches
"""

import re
from typing import Any, Dict, List, Optional, TypedDict

from compliancepack.policy import PolicyDict, PolicyFileDict, get_severity_rank
from compliancepack.redact import create_excerpt


class MatchDict(TypedDict):
    """A single match occurrence."""
    line: int
    col_start: int
    col_end: int
    excerpt: str


class FindingDict(TypedDict):
    """A finding for a single policy."""
    id: str
    title: str
    severity: str
    description: str
    match_count: int
    samples: List[MatchDict]


class SeverityCountsDict(TypedDict):
    """Severity counts for summary."""
    critical: int
    high: int
    medium: int
    low: int
    info: int


class SummaryDict(TypedDict):
    """Summary of check results."""
    policy_count: int
    finding_count: int
    severity_counts: SeverityCountsDict


class CheckResultDict(TypedDict):
    """Complete check result output."""
    format: str
    generated_at_utc: str
    input_path: str
    policy_path: str
    redaction_applied: bool
    summary: SummaryDict
    findings: List[FindingDict]


def _find_regex_matches(
    lines: List[str],
    pattern: str,
    sample_limit: int,
    apply_redaction: bool,
) -> List[MatchDict]:
    """
    Find regex matches across all lines.

    Args:
        lines: List of lines (0-indexed internally, 1-indexed in output)
        pattern: Regex pattern to match
        sample_limit: Maximum samples to return
        apply_redaction: Whether to redact excerpts

    Returns:
        List of matches, sorted by line then col_start, capped at sample_limit
    """
    compiled = re.compile(pattern)
    matches: List[MatchDict] = []

    for line_idx, line in enumerate(lines):
        line_num = line_idx + 1  # 1-indexed
        for match in compiled.finditer(line):
            matches.append({
                "line": line_num,
                "col_start": match.start(),
                "col_end": match.end(),
                "excerpt": create_excerpt(
                    line,
                    match.start(),
                    match.end(),
                    apply_redaction=apply_redaction,
                ),
            })

    # Sort by line, then col_start for deterministic ordering
    matches.sort(key=lambda m: (m["line"], m["col_start"]))

    # Cap at sample_limit
    return matches[:sample_limit]


def _find_contains_matches(
    lines: List[str],
    needle: str,
    sample_limit: int,
    apply_redaction: bool,
) -> List[MatchDict]:
    """
    Find substring occurrences across all lines.

    Args:
        lines: List of lines (0-indexed internally, 1-indexed in output)
        needle: Substring to find
        sample_limit: Maximum samples to return
        apply_redaction: Whether to redact excerpts

    Returns:
        List of matches, sorted by line then col_start, capped at sample_limit
    """
    matches: List[MatchDict] = []

    for line_idx, line in enumerate(lines):
        line_num = line_idx + 1  # 1-indexed
        start = 0
        while True:
            pos = line.find(needle, start)
            if pos == -1:
                break
            matches.append({
                "line": line_num,
                "col_start": pos,
                "col_end": pos + len(needle),
                "excerpt": create_excerpt(
                    line,
                    pos,
                    pos + len(needle),
                    apply_redaction=apply_redaction,
                ),
            })
            start = pos + 1  # Continue searching after this match

    # Sort by line, then col_start for deterministic ordering
    matches.sort(key=lambda m: (m["line"], m["col_start"]))

    # Cap at sample_limit
    return matches[:sample_limit]


def apply_policy(
    lines: List[str],
    policy: PolicyDict,
    apply_redaction: bool,
) -> Optional[FindingDict]:
    """
    Apply a single policy to input lines.

    Args:
        lines: List of lines from input file
        policy: Policy to apply
        apply_redaction: Whether to redact excerpts

    Returns:
        FindingDict if matches found, None otherwise
    """
    sample_limit = policy["sample_limit"]

    if policy["type"] == "regex":
        matches = _find_regex_matches(
            lines,
            policy["pattern"],
            sample_limit,
            apply_redaction,
        )
    elif policy["type"] == "contains":
        matches = _find_contains_matches(
            lines,
            policy["needle"],
            sample_limit,
            apply_redaction,
        )
    else:
        # Unknown type - should not happen if validation is correct
        return None

    if not matches:
        return None

    # Count total matches (before sample_limit truncation)
    # Re-count without limit to get accurate count
    if policy["type"] == "regex":
        total_matches = sum(
            len(list(re.finditer(policy["pattern"], line)))
            for line in lines
        )
    else:
        total_matches = sum(
            line.count(policy["needle"])
            for line in lines
        )

    return {
        "id": policy["id"],
        "title": policy["title"],
        "severity": policy["severity"],
        "description": policy["description"],
        "match_count": total_matches,
        "samples": matches,
    }


def run_check(
    input_path: str,
    policy_file: PolicyFileDict,
    policy_path: str,
    generated_at_utc: str,
    apply_redaction: bool = True,
) -> CheckResultDict:
    """
    Run compliance check on input file.

    Args:
        input_path: Path to input file
        policy_file: Loaded and validated policy file
        policy_path: Original path to policy file (for output)
        generated_at_utc: Timestamp for output
        apply_redaction: Whether to apply redaction to excerpts

    Returns:
        Complete CheckResultDict ready for JSON serialization
    """
    # Read input file
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = content.splitlines()

    # Apply each policy
    findings: List[FindingDict] = []
    for policy in policy_file["policies"]:
        finding = apply_policy(lines, policy, apply_redaction)
        if finding:
            findings.append(finding)

    # Sort findings by severity (most severe first), then by id
    findings.sort(key=lambda f: (get_severity_rank(f["severity"]), f["id"]))

    # Calculate severity counts
    severity_counts: SeverityCountsDict = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }
    for finding in findings:
        severity = finding["severity"]
        if severity in severity_counts:
            severity_counts[severity] += 1

    # Build result
    return {
        "format": "compliancepack.check.v1",
        "generated_at_utc": generated_at_utc,
        "input_path": input_path,
        "policy_path": policy_path,
        "redaction_applied": apply_redaction,
        "summary": {
            "policy_count": len(policy_file["policies"]),
            "finding_count": len(findings),
            "severity_counts": severity_counts,
        },
        "findings": findings,
    }
