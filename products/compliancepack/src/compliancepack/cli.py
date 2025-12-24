"""
CompliancePack CLI implementation.

Provides the `check` subcommand for compliance analysis.

Contract:
- --input <path>: Required, read-only file path
- --fixed-time <ISO8601Z>: Optional, deterministic timestamp
- --redact/--no-redact: Optional, redaction control (default: ON)
- Output: JSON to stdout, stable formatting
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from compliancepack import __version__
from compliancepack.model import CheckResult, create_check_result


def _get_timestamp(fixed_time: Optional[str] = None) -> str:
    """Get timestamp for output, using fixed time if provided."""
    if fixed_time:
        return fixed_time
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _output_json(data: Dict[str, Any]) -> None:
    """Output JSON with stable formatting (deterministic)."""
    json_str = json.dumps(data, sort_keys=True, separators=(",", ":"))
    print(json_str)


def cmd_check(args: argparse.Namespace) -> int:
    """Execute the 'check' subcommand."""
    input_path = Path(args.input)

    # Validate input file exists (read-only check)
    if not input_path.exists():
        sys.stderr.write(f"Error: Input file not found: {args.input}\n")
        return 1

    if not input_path.is_file():
        sys.stderr.write(f"Error: Input path is not a file: {args.input}\n")
        return 1

    # Get timestamp
    timestamp = _get_timestamp(args.fixed_time)

    # Create check result (scaffold - no actual checks yet)
    result = create_check_result(
        input_file=str(input_path),
        generated_at_utc=timestamp,
        redact=args.redact,
    )

    # Output JSON to stdout
    _output_json(result)

    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        prog="compliancepack",
        description="Contract-first compliance evidence toolkit",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # check subcommand
    check_parser = subparsers.add_parser(
        "check",
        help="Analyze configuration files for compliance violations",
    )
    check_parser.add_argument(
        "--input",
        required=True,
        help="Path to input file (read-only)",
    )
    check_parser.add_argument(
        "--fixed-time",
        metavar="ISO8601Z",
        help="Fixed timestamp for deterministic output (e.g., 2025-01-01T00:00:00Z)",
    )
    check_parser.add_argument(
        "--redact",
        dest="redact",
        action="store_true",
        default=True,
        help="Redact sensitive values in output (default: ON)",
    )
    check_parser.add_argument(
        "--no-redact",
        dest="redact",
        action="store_false",
        help="Disable redaction of sensitive values",
    )

    return parser


def main() -> None:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "check":
        sys.exit(cmd_check(args))
    else:
        parser.print_help()
        sys.exit(1)
