"""
CompliancePack CLI implementation.

Provides the `check` subcommand for compliance analysis.

Contract:
- --input <path>: Required, read-only file path
- --policy <path> OR --pack <name>: Exactly one required (mutually exclusive)
- --list-packs: List available packs and exit
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
from compliancepack.engine import run_check
from compliancepack.packs import PackError, get_pack_path, list_packs, load_pack
from compliancepack.policy import PolicyValidationError, load_policy_file


def _get_timestamp(fixed_time: Optional[str] = None) -> str:
    """Get timestamp for output, using fixed time if provided."""
    if fixed_time:
        return fixed_time
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _output_json(data: Dict[str, Any]) -> None:
    """Output JSON with stable formatting (deterministic)."""
    json_str = json.dumps(data, sort_keys=True, separators=(",", ": "), ensure_ascii=False)
    print(json_str)


def cmd_list_packs() -> int:
    """List available packs and exit."""
    packs = list_packs()

    if not packs:
        print("No packs available.")
    else:
        print("Available packs:")
        for pack in packs:
            print(f"  {pack}")

    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Execute the 'check' subcommand."""
    # Handle --list-packs first
    if getattr(args, "list_packs", False):
        return cmd_list_packs()

    input_path = Path(args.input)

    # Validate input file exists (read-only check)
    if not input_path.exists():
        sys.stderr.write(f"Error: Input file not found: {args.input}\n")
        return 1

    if not input_path.is_file():
        sys.stderr.write(f"Error: Input path is not a file: {args.input}\n")
        return 1

    # Determine policy source: --policy or --pack (mutually exclusive)
    policy = getattr(args, "policy", None)
    pack = getattr(args, "pack", None)

    if policy and pack:
        sys.stderr.write("Error: Cannot specify both --policy and --pack\n")
        return 2

    if not policy and not pack:
        sys.stderr.write("Error: Must specify either --policy or --pack\n")
        return 2

    # Load policy from file or pack
    if policy:
        policy_path = Path(policy)

        if not policy_path.exists():
            sys.stderr.write(f"Error: Policy file not found: {policy}\n")
            return 1

        if not policy_path.is_file():
            sys.stderr.write(f"Error: Policy path is not a file: {policy}\n")
            return 1

        try:
            policy_file = load_policy_file(policy_path)
            policy_path_str = str(policy_path)
        except PolicyValidationError as e:
            sys.stderr.write(f"Error: Policy validation failed: {e}\n")
            return 1
        except json.JSONDecodeError as e:
            sys.stderr.write(f"Error: Invalid JSON in policy file: {e}\n")
            return 1
    else:
        # Load from pack
        try:
            policy_file = load_pack(pack)
            policy_path_str = f"pack:{pack}"
        except PackError as e:
            sys.stderr.write(f"Error: {e}\n")
            return 1
        except PolicyValidationError as e:
            sys.stderr.write(f"Error: Pack validation failed: {e}\n")
            return 1

    # Get timestamp
    timestamp = _get_timestamp(args.fixed_time)

    # Run check
    result = run_check(
        input_path=str(input_path),
        policy_file=policy_file,
        policy_path=policy_path_str,
        generated_at_utc=timestamp,
        apply_redaction=args.redact,
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
        help="Path to input file (read-only)",
    )

    # Policy source: mutually exclusive --policy and --pack
    policy_group = check_parser.add_mutually_exclusive_group()
    policy_group.add_argument(
        "--policy",
        metavar="PATH",
        help="Path to custom JSON policy file",
    )
    policy_group.add_argument(
        "--pack",
        metavar="NAME",
        help="Use built-in policy pack (e.g., secrets.v1, pii.v1)",
    )

    check_parser.add_argument(
        "--list-packs",
        action="store_true",
        help="List available built-in packs and exit",
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
        # Handle --list-packs specially (no --input required)
        if getattr(args, "list_packs", False):
            sys.exit(cmd_list_packs())

        # Otherwise, --input is required
        if not args.input:
            sys.stderr.write("Error: --input is required for check command\n")
            sys.exit(2)

        sys.exit(cmd_check(args))
    else:
        parser.print_help()
        sys.exit(1)
