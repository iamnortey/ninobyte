"""
CLI for lexicon pack management.

Commands:
- validate: Validate a pack against schema
- show: Display pack metadata and entries
- lock: Generate lockfile for a pack
- verify: Verify pack matches its lockfile
- discover: Discover packs in a directory
- verify-all: Verify all packs in a directory
"""

import argparse
import sys
from pathlib import Path

from lexicon_packs import __version__
from lexicon_packs.canonicalize import canonicalize_json
from lexicon_packs.validate import validate_pack
from lexicon_packs.load import load_pack, LoadError
from lexicon_packs.lockfile import (
    generate_lockfile,
    format_lockfile_json,
    verify_lockfile,
    write_lockfile,
    LockfileError,
)
from lexicon_packs.discover import (
    discover_packs,
    discover_packs_with_info,
    format_discovery_json,
    verify_all_packs,
    DiscoveryError,
)


def main(argv: list[str] | None = None) -> int:
    """
    Main CLI entry point.

    Args:
        argv: Command line arguments (default: sys.argv[1:])

    Returns:
        Exit code (0 = success, 2 = error)
    """
    parser = argparse.ArgumentParser(
        prog="lexicon-packs",
        description="Lexicon pack validation and management",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"ninobyte-lexicon-packs {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a lexicon pack",
    )
    validate_parser.add_argument(
        "--pack",
        required=True,
        help="Path to pack directory",
    )

    # show command
    show_parser = subparsers.add_parser(
        "show",
        help="Display pack metadata",
    )
    show_parser.add_argument(
        "--pack",
        required=True,
        help="Path to pack directory",
    )
    show_parser.add_argument(
        "--output",
        choices=["json"],
        required=True,
        help="Output format",
    )
    show_parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of entries to include (default: 5)",
    )

    # lock command
    lock_parser = subparsers.add_parser(
        "lock",
        help="Generate lockfile for a pack",
    )
    lock_parser.add_argument(
        "--pack",
        required=True,
        help="Path to pack directory",
    )
    lock_parser.add_argument(
        "--write",
        action="store_true",
        help="Write lockfile to pack directory instead of stdout",
    )
    lock_parser.add_argument(
        "--fixed-time",
        help="Fixed UTC timestamp for deterministic output (ISO 8601)",
    )

    # verify command
    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify pack matches its lockfile",
    )
    verify_parser.add_argument(
        "--pack",
        required=True,
        help="Path to pack directory",
    )

    # discover command
    discover_parser = subparsers.add_parser(
        "discover",
        help="Discover packs in a directory",
    )
    discover_parser.add_argument(
        "--root",
        help="Root directory to search (default: packs/)",
    )
    discover_parser.add_argument(
        "--output",
        choices=["json"],
        default="json",
        help="Output format (default: json)",
    )
    discover_parser.add_argument(
        "--fixed-time",
        help="Fixed UTC timestamp for deterministic output (ISO 8601)",
    )

    # verify-all command
    verify_all_parser = subparsers.add_parser(
        "verify-all",
        help="Verify all packs in a directory",
    )
    verify_all_parser.add_argument(
        "--root",
        help="Root directory to search (default: packs/)",
    )

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 2

    if args.command == "validate":
        return cmd_validate(args)
    elif args.command == "show":
        return cmd_show(args)
    elif args.command == "lock":
        return cmd_lock(args)
    elif args.command == "verify":
        return cmd_verify(args)
    elif args.command == "discover":
        return cmd_discover(args)
    elif args.command == "verify-all":
        return cmd_verify_all(args)

    parser.print_help()
    return 2


def cmd_validate(args: argparse.Namespace) -> int:
    """Execute the validate command."""
    pack_path = Path(args.pack)

    # Path traversal check
    if ".." in str(pack_path):
        print(f"Error: Path traversal not allowed: {pack_path}", file=sys.stderr)
        return 2

    result = validate_pack(pack_path)

    if result.valid:
        print(f"Pack valid: {result.pack_path}")
        return 0
    else:
        print(f"Pack invalid: {result.pack_path}", file=sys.stderr)
        for error in result.errors:
            print(f"  - {error}", file=sys.stderr)
        return 2


def cmd_show(args: argparse.Namespace) -> int:
    """Execute the show command."""
    pack_path = Path(args.pack)

    # Path traversal check
    if ".." in str(pack_path):
        print(f"Error: Path traversal not allowed: {pack_path}", file=sys.stderr)
        return 2

    try:
        pack = load_pack(pack_path)
    except LoadError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    # Build output
    output = pack.to_dict(include_entries=args.limit)

    # Output as canonical JSON
    print(canonicalize_json(output), end="")
    return 0


def cmd_lock(args: argparse.Namespace) -> int:
    """Execute the lock command."""
    pack_path = Path(args.pack).resolve()

    # Ensure pack directory exists
    if not pack_path.is_dir():
        print(f"Error: Pack directory not found: {pack_path}", file=sys.stderr)
        return 2

    fixed_time = getattr(args, "fixed_time", None)

    try:
        if args.write:
            lockfile_path = write_lockfile(pack_path, fixed_time=fixed_time)
            print(f"Lockfile written: {lockfile_path}")
            return 0
        else:
            lockfile = generate_lockfile(pack_path, fixed_time=fixed_time)
            print(format_lockfile_json(lockfile), end="")
            return 0
    except LockfileError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


def cmd_verify(args: argparse.Namespace) -> int:
    """Execute the verify command."""
    pack_path = Path(args.pack).resolve()

    # Ensure pack directory exists
    if not pack_path.is_dir():
        print(f"Error: Pack directory not found: {pack_path}", file=sys.stderr)
        return 2

    is_valid, errors = verify_lockfile(pack_path)

    if is_valid:
        print(f"Lockfile verified: {pack_path}")
        return 0
    else:
        print(f"Lockfile verification failed: {pack_path}", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 2


def cmd_discover(args: argparse.Namespace) -> int:
    """Execute the discover command."""
    # Determine root directory
    if args.root:
        root = Path(args.root).resolve()
    else:
        # Default to packs/ relative to current directory
        root = Path.cwd() / "packs"

    # Validate root exists
    if not root.exists():
        print(f"Error: Root directory not found: {root}", file=sys.stderr)
        return 2

    if not root.is_dir():
        print(f"Error: Root is not a directory: {root}", file=sys.stderr)
        return 2

    fixed_time = getattr(args, "fixed_time", None)

    try:
        packs = discover_packs_with_info(root, relative_to=root)
    except DiscoveryError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    # Check for packs with errors
    has_errors = any(p.error is not None for p in packs)

    # Output JSON
    print(format_discovery_json(packs, fixed_time=fixed_time), end="")

    # Return 2 if any packs have errors
    return 2 if has_errors else 0


def cmd_verify_all(args: argparse.Namespace) -> int:
    """Execute the verify-all command."""
    # Determine root directory
    if args.root:
        root = Path(args.root).resolve()
    else:
        # Default to packs/ relative to current directory
        root = Path.cwd() / "packs"

    # Validate root exists
    if not root.exists():
        print(f"Error: Root directory not found: {root}", file=sys.stderr)
        return 2

    if not root.is_dir():
        print(f"Error: Root is not a directory: {root}", file=sys.stderr)
        return 2

    try:
        all_valid, results = verify_all_packs(root, fail_fast=True)
    except DiscoveryError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    if not results:
        print("No packs found to verify")
        return 0

    # Print results
    for result in results:
        if result.valid:
            print(f"  {result.pack_id}: verified")
        else:
            print(f"  {result.pack_id}: FAILED", file=sys.stderr)
            for error in result.errors:
                print(f"    - {error}", file=sys.stderr)

    # Summary
    verified_count = sum(1 for r in results if r.valid)
    failed_count = sum(1 for r in results if not r.valid)

    print()
    if all_valid:
        print(f"Verified {verified_count} pack(s)")
        return 0
    else:
        print(f"Verification failed: {failed_count} pack(s) failed, {verified_count} passed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
