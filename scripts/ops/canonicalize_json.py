#!/usr/bin/env python3
"""Canonicalize JSON for deterministic hashing.

Produces a stable, reproducible JSON representation independent of
field ordering or whitespace variations in the input.

Usage:
    python3 canonicalize_json.py --in <input.json> --out <output.json>
    python3 canonicalize_json.py --in <input.json>  # writes to stdout
"""

import argparse
import json
import sys
from pathlib import Path


def canonicalize(data: object) -> str:
    """Return canonical JSON string with trailing newline.

    Canonical format:
    - Keys sorted recursively
    - Compact separators (no extra whitespace)
    - Unicode preserved (no ASCII escaping)
    - Single trailing newline
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Canonicalize JSON for deterministic SHA256 hashing.",
        epilog="Exits nonzero on invalid JSON input.",
    )
    parser.add_argument(
        "--in",
        dest="input_file",
        required=True,
        help="Path to input JSON file",
    )
    parser.add_argument(
        "--out",
        dest="output_file",
        help="Path to output file (default: stdout)",
    )

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return 1

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {input_path}: {e}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"Error: Cannot read {input_path}: {e}", file=sys.stderr)
        return 1

    canonical = canonicalize(data)

    if args.output_file:
        output_path = Path(args.output_file)
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(canonical)
            print(f"Wrote canonical JSON to: {output_path}")
        except OSError as e:
            print(f"Error: Cannot write {output_path}: {e}", file=sys.stderr)
            return 1
    else:
        sys.stdout.write(canonical)

    return 0


if __name__ == "__main__":
    sys.exit(main())
