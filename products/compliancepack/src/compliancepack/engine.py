"""
CompliancePack Matcher Engine.

Applies policies to input text with deterministic matching and ordering.

Matching semantics:
- Read input as lines with stable line numbers (1-indexed)
- For regex: re.finditer per line
- For contains: find substring occurrences per line
- Store matches with line, col_start, col_end, excerpt

Deterministic ordering (single file):
- Findings sorted by: severity rank (asc = more severe first), then policy id
- Matches sorted by: line asc, col_start asc
- Samples capped by sample_limit, taking earliest matches

Deterministic ordering (multi-file):
- Findings sorted by: severity rank desc -> id asc -> file asc -> line asc -> col_start asc
- Samples sorted by: file asc -> line asc -> col_start asc
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TypedDict

from compliancepack.policy import PolicyDict, PolicyFileDict, get_severity_rank
from compliancepack.redact import create_excerpt


class MatchDict(TypedDict, total=False):
    """A single match occurrence."""
    line: int
    col_start: int
    col_end: int
    excerpt: str
    file: str  # Present in multi-file mode


class FindingDict(TypedDict, total=False):
    """A finding for a single policy."""
    id: str
    title: str
    severity: str
    description: str
    match_count: int
    samples: List[MatchDict]
    file: str  # Present in single-file mode for multi-file scans


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


def _find_regex_matches_with_file(
    lines: List[str],
    pattern: str,
    sample_limit: int,
    apply_redaction: bool,
    file_path: str,
) -> Tuple[List[MatchDict], int]:
    """
    Find regex matches across all lines, including file path in each match.

    Returns:
        Tuple of (matches, total_count)
    """
    compiled = re.compile(pattern)
    matches: List[MatchDict] = []
    total_count = 0

    for line_idx, line in enumerate(lines):
        line_num = line_idx + 1
        for match in compiled.finditer(line):
            total_count += 1
            if len(matches) < sample_limit:
                matches.append({
                    "file": file_path,
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

    return matches, total_count


def _find_contains_matches_with_file(
    lines: List[str],
    needle: str,
    sample_limit: int,
    apply_redaction: bool,
    file_path: str,
) -> Tuple[List[MatchDict], int]:
    """
    Find substring occurrences across all lines, including file path in each match.

    Returns:
        Tuple of (matches, total_count)
    """
    matches: List[MatchDict] = []
    total_count = 0

    for line_idx, line in enumerate(lines):
        line_num = line_idx + 1
        start = 0
        while True:
            pos = line.find(needle, start)
            if pos == -1:
                break
            total_count += 1
            if len(matches) < sample_limit:
                matches.append({
                    "file": file_path,
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
            start = pos + 1

    return matches, total_count


def apply_policy_to_file(
    content: str,
    file_path: str,
    policy: PolicyDict,
    apply_redaction: bool,
) -> Tuple[List[MatchDict], int]:
    """
    Apply a single policy to file content.

    Returns:
        Tuple of (matches, total_count)
    """
    lines = content.splitlines()
    sample_limit = policy["sample_limit"]

    if policy["type"] == "regex":
        return _find_regex_matches_with_file(
            lines, policy["pattern"], sample_limit, apply_redaction, file_path
        )
    elif policy["type"] == "contains":
        return _find_contains_matches_with_file(
            lines, policy["needle"], sample_limit, apply_redaction, file_path
        )
    else:
        return [], 0


class MultiFileCheckResult(TypedDict):
    """Result from multi-file check."""
    format: str
    generated_at_utc: str
    inputs: List[str]
    policy_path: str
    redaction_applied: bool
    summary: Dict[str, Any]
    scan_stats: Dict[str, Any]
    findings: List[FindingDict]


def run_check_multi(
    files: List[Path],
    file_contents: Dict[str, str],
    input_roots: List[str],
    policy_file: PolicyFileDict,
    policy_path: str,
    generated_at_utc: str,
    apply_redaction: bool = True,
    files_skipped_summary: Optional[Dict[str, int]] = None,
) -> MultiFileCheckResult:
    """
    Run compliance check on multiple files.

    Args:
        files: List of file paths to check (sorted, canonical)
        file_contents: Dict mapping file path string to content
        input_roots: Original input paths (for output)
        policy_file: Loaded and validated policy file
        policy_path: Original path to policy file (for output)
        generated_at_utc: Timestamp for output
        apply_redaction: Whether to apply redaction to excerpts
        files_skipped_summary: Optional dict of skip reasons -> counts

    Returns:
        MultiFileCheckResult ready for JSON serialization
    """
    # Aggregate findings across all files
    # Key: policy_id -> aggregated finding
    policy_findings: Dict[str, Dict[str, Any]] = {}

    files_scanned = 0
    files_with_findings = 0

    for file_path in files:
        file_str = str(file_path)
        content = file_contents.get(file_str, "")
        files_scanned += 1
        file_had_finding = False

        for policy in policy_file["policies"]:
            matches, total_count = apply_policy_to_file(
                content, file_str, policy, apply_redaction
            )

            if total_count > 0:
                file_had_finding = True
                policy_id = policy["id"]

                if policy_id not in policy_findings:
                    policy_findings[policy_id] = {
                        "id": policy_id,
                        "title": policy["title"],
                        "severity": policy["severity"],
                        "description": policy["description"],
                        "match_count": 0,
                        "samples": [],
                    }

                policy_findings[policy_id]["match_count"] += total_count
                # Add samples up to limit
                current_samples = policy_findings[policy_id]["samples"]
                remaining = policy["sample_limit"] - len(current_samples)
                if remaining > 0:
                    policy_findings[policy_id]["samples"].extend(matches[:remaining])

        if file_had_finding:
            files_with_findings += 1

    # Convert to list and sort
    findings: List[FindingDict] = list(policy_findings.values())

    # Sort samples within each finding: file -> line -> col_start
    for finding in findings:
        finding["samples"].sort(
            key=lambda m: (m.get("file", ""), m["line"], m["col_start"])
        )

    # Sort findings: severity rank (lower = more severe) -> id -> first file
    def finding_sort_key(f: Dict) -> Tuple:
        first_file = f["samples"][0]["file"] if f["samples"] else ""
        return (get_severity_rank(f["severity"]), f["id"], first_file)

    findings.sort(key=finding_sort_key)

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

    # Build scan stats
    scan_stats: Dict[str, Any] = {
        "files_scanned": files_scanned,
        "files_with_findings": files_with_findings,
    }
    if files_skipped_summary:
        scan_stats["files_skipped"] = files_skipped_summary

    return {
        "format": "compliancepack.check.v1",
        "generated_at_utc": generated_at_utc,
        "inputs": sorted(input_roots),
        "policy_path": policy_path,
        "redaction_applied": apply_redaction,
        "summary": {
            "policy_count": len(policy_file["policies"]),
            "finding_count": len(findings),
            "severity_counts": severity_counts,
        },
        "scan_stats": scan_stats,
        "findings": findings,
    }
