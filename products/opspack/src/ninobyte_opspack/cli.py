"""
Ninobyte OpsPack CLI

Command-line interface for OpsPack operations.
Read-only, deterministic, no network, no shell execution.

Usage:
    ninobyte-opspack incident-triage --input <path-to-json> [--format json]
    python -m ninobyte_opspack incident-triage --input <path-to-json> [--format json]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from .triage import triage_incident
from .version import __version__


def _read_json_file(path: str) -> dict:
    """
    Read and parse a JSON file.

    Args:
        path: Path to JSON file

    Returns:
        Parsed JSON as dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
        PermissionError: If file is not readable
    """
    filepath = Path(path).resolve()

    if not filepath.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    if not filepath.is_file():
        raise ValueError(f"Input path is not a file: {path}")

    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_incident_triage(args: argparse.Namespace) -> int:
    """
    Execute incident-triage command.

    Reads incident snapshot from JSON file and outputs triage summary.
    """
    try:
        # Read input file
        incident = _read_json_file(args.input)

        # Perform triage
        result = triage_incident(incident)

        # Output result
        if args.format == "json":
            # Deterministic output: sorted keys, consistent indentation
            output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)
            print(output)
        else:
            # Default to JSON for now (only supported format in MVP)
            output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)
            print(output)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}", file=sys.stderr)
        return 1
    except PermissionError as e:
        print(f"Error: Cannot read input file: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="ninobyte-opspack",
        description="Ninobyte OpsPack - Read-Only Operational Intelligence Module",
        epilog="Security: Read-only, no network, no shell execution."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(
        title="commands",
        dest="command",
        required=True
    )

    # incident-triage command
    triage_parser = subparsers.add_parser(
        "incident-triage",
        help="Analyze an incident snapshot and produce a triage summary",
        description=(
            "Read an incident snapshot from a JSON file and produce a deterministic "
            "triage summary with classification, recommended actions, and risk flags."
        )
    )
    triage_parser.add_argument(
        "--input",
        required=True,
        metavar="PATH",
        help="Path to JSON file containing incident snapshot"
    )
    triage_parser.add_argument(
        "--format",
        choices=["json"],
        default="json",
        help="Output format (default: json)"
    )
    triage_parser.set_defaults(func=cmd_incident_triage)

    return parser


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    if hasattr(args, "func"):
        return args.func(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
