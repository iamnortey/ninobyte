"""
CLI interface for OpsPack.

Entry point: python -m opspack

Security guarantees:
- No network calls
- No shell execution
- Redaction applied by default
- Deterministic outputs
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Set

from opspack import __version__
from opspack.model import TRIAGE_SCHEMA_VERSION, TriageResult, TriageSignals
from opspack.redact import redact_text


def _find_repo_root() -> Optional[Path]:
    """Find the repository root by looking for .git directory."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
    return None


def _make_path_repo_relative(path: Path, repo_root: Optional[Path]) -> tuple:
    """
    Convert path to repo-relative if possible.

    Returns:
        Tuple of (path_string, path_type)
    """
    if repo_root is None:
        return (str(path.resolve()), "absolute")

    try:
        relative = path.resolve().relative_to(repo_root)
        return (str(relative), "repo-relative")
    except ValueError:
        return (str(path.resolve()), "absolute")


def _extract_timestamps(text: str) -> Set[str]:
    """Extract timestamp-like patterns from text."""
    patterns = [
        # ISO 8601 formats
        re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"),
        re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"),
        # Common log formats
        re.compile(r"\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}"),
        # Unix timestamps (10-13 digits)
        re.compile(r"\b\d{10,13}\b"),
    ]
    matches: Set[str] = set()
    for pattern in patterns:
        matches.update(pattern.findall(text))
    return matches


def _extract_error_keywords(text: str) -> Set[str]:
    """Extract error-related keywords from text."""
    keywords = [
        "error", "exception", "failed", "failure", "fatal",
        "critical", "panic", "crash", "timeout", "refused",
        "denied", "unauthorized", "forbidden", "not found",
        "null", "undefined", "segfault", "oom", "killed"
    ]
    found: Set[str] = set()
    text_lower = text.lower()
    for keyword in keywords:
        if keyword in text_lower:
            found.add(keyword)
    return found


def _extract_stacktrace_markers(text: str) -> Set[str]:
    """Extract stacktrace-like patterns from text."""
    patterns = [
        re.compile(r"at .+\(.+:\d+\)"),  # Java/JS style
        re.compile(r'File ".+", line \d+'),  # Python style
        re.compile(r"\w+\.go:\d+"),  # Go style
        re.compile(r"Traceback \(most recent call"),  # Python traceback
        re.compile(r"^\s+at\s+", re.MULTILINE),  # Generic "at" lines
    ]
    found: Set[str] = set()
    for pattern in patterns:
        matches = pattern.findall(text)
        if matches:
            # Normalize to just the pattern type found
            found.add(pattern.pattern[:20] + "...")
    return found


def cmd_triage(args: argparse.Namespace) -> int:
    """Execute the triage command."""
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return 1

    if not input_path.is_file():
        print(f"Error: Input path is not a file: {input_path}", file=sys.stderr)
        return 1

    # Read input file
    try:
        content = input_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Try with latin-1 as fallback
        content = input_path.read_text(encoding="latin-1")
    except OSError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return 1

    # Apply redaction by default (unless explicitly disabled)
    redaction_applied = not args.no_redact
    if redaction_applied:
        content = redact_text(content)

    # Extract signals
    signals = TriageSignals(
        timestamps=list(_extract_timestamps(content)),
        error_keywords=list(_extract_error_keywords(content)),
        stacktrace_markers=list(_extract_stacktrace_markers(content)),
    )

    # Determine path representation
    repo_root = _find_repo_root()
    path_str, path_type = _make_path_repo_relative(input_path, repo_root)

    # Generate timestamp (or use fixed time for determinism in tests)
    if args.fixed_time:
        generated_at = args.fixed_time
    else:
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build result
    result = TriageResult(
        schema_version=TRIAGE_SCHEMA_VERSION,
        generated_at_utc=generated_at,
        input_path=path_str,
        input_path_type=path_type,
        redaction_applied=redaction_applied,
        signals=signals,
        line_count=content.count("\n") + (1 if content and not content.endswith("\n") else 0),
        char_count=len(content),
    )

    # Output as JSON (deterministic: sorted keys, consistent indent)
    output = json.dumps(result.to_dict(), indent=2, sort_keys=True)

    if args.output_file:
        Path(args.output_file).write_text(output + "\n", encoding="utf-8")
        print(f"Output written to: {args.output_file}")
    else:
        print(output)

    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="opspack",
        description="OpsPack: Deterministic incident triage and log analysis toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Security Guarantees:
  - No network calls
  - No shell execution
  - Redaction applied by default
  - Deterministic outputs for reproducibility

Examples:
  opspack triage --input incident.log --output json
  opspack triage --input /var/log/app.log --output-file report.json
"""
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Triage command
    triage_parser = subparsers.add_parser(
        "triage",
        help="Analyze incident logs and produce structured triage report"
    )
    triage_parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to input file (log file, incident notes, etc.)"
    )
    triage_parser.add_argument(
        "--output", "-o",
        choices=["json"],
        default="json",
        help="Output format (default: json)"
    )
    triage_parser.add_argument(
        "--output-file", "-f",
        help="Write output to file instead of stdout"
    )
    triage_parser.add_argument(
        "--no-redact",
        action="store_true",
        help="Disable automatic redaction (NOT RECOMMENDED)"
    )
    triage_parser.add_argument(
        "--fixed-time",
        help=argparse.SUPPRESS  # Hidden arg for deterministic testing
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "triage":
        return cmd_triage(args)

    # Unknown command (shouldn't happen with subparsers)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
