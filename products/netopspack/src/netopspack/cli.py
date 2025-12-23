"""
CLI for NetOpsPack network operations toolkit.

Commands:
- diagnose: Analyze network logs and produce structured diagnostic output
"""

import argparse
import sys

from netopspack import __version__
from netopspack.diagnose import diagnose_file, format_report_json


def main(argv: list[str] | None = None) -> int:
    """
    Main CLI entry point.

    Args:
        argv: Command line arguments (default: sys.argv[1:])

    Returns:
        Exit code (0 = success, 2 = error)
    """
    parser = argparse.ArgumentParser(
        prog="netopspack",
        description="Network operations toolkit for SRE/DevOps incident triage",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"ninobyte-netopspack {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # diagnose command
    diagnose_parser = subparsers.add_parser(
        "diagnose",
        help="Analyze network logs and produce structured diagnostics",
    )
    diagnose_parser.add_argument(
        "--input",
        required=True,
        help="Path to log file to analyze",
    )
    diagnose_parser.add_argument(
        "--format",
        choices=["syslog", "nginx", "haproxy"],
        default="syslog",
        help="Log format (default: syslog)",
    )
    diagnose_parser.add_argument(
        "--fixed-time",
        help="Fixed UTC timestamp for deterministic output (ISO 8601)",
    )
    diagnose_parser.add_argument(
        "--output",
        choices=["json"],
        default="json",
        help="Output format (default: json)",
    )
    diagnose_parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of events to include (default: 50)",
    )
    diagnose_parser.add_argument(
        "--redact",
        action="store_true",
        default=True,
        help="Apply redaction to sensitive data (default: enabled)",
    )
    diagnose_parser.add_argument(
        "--no-redact",
        action="store_true",
        help="Disable redaction",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 2

    if args.command == "diagnose":
        return cmd_diagnose(args)

    parser.print_help()
    return 2


def cmd_diagnose(args: argparse.Namespace) -> int:
    """
    Execute the diagnose command.

    Analyzes a log file and outputs a deterministic JSON report.
    """
    # Determine redaction setting
    redact = not args.no_redact

    try:
        report = diagnose_file(
            input_path=args.input,
            format=args.format,
            fixed_time=args.fixed_time,
            limit=args.limit,
            redact=redact,
        )

        # Output JSON (already newline-terminated)
        print(format_report_json(report), end="")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
