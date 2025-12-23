"""
CLI for lexicon pack management.

Commands:
- validate: Validate a pack against schema
- show: Display pack metadata and entries
"""

import argparse
import sys
from pathlib import Path

from lexicon_packs import __version__
from lexicon_packs.canonicalize import canonicalize_json
from lexicon_packs.validate import validate_pack
from lexicon_packs.load import load_pack, LoadError


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

    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 2

    if args.command == "validate":
        return cmd_validate(args)
    elif args.command == "show":
        return cmd_show(args)

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


if __name__ == "__main__":
    sys.exit(main())
