#!/usr/bin/env python3
"""
JSONL consumer compatibility check for ninobyte-context-cleaner.

Validates that JSONL output conforms to the schema v1 contract
from a downstream consumer's perspective.

This simulates what a real consumer would do:
1. Read exactly one JSONL line from stdin
2. Parse with stdlib json.loads()
3. Validate required keys and types

Security:
- No networking imports
- No file writes
- Stdlib only (json, sys)

Exit Codes:
    0   CONSUMER: PASS
    2   CONSUMER: FAIL (with Error: message)

Usage:
    echo "input" | ninobyte-context-cleaner --output-format jsonl | python jsonl_consumer_check.py
"""

import json
import sys


def validate_jsonl(line: str) -> tuple:
    """
    Validate a single JSONL line against schema v1 contract.

    Args:
        line: Raw JSONL line (may include trailing newline)

    Returns:
        (passed: bool, error_message: str or None)
    """
    # Parse JSON
    try:
        data = json.loads(line.strip())
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"

    # Validate required keys exist
    required_keys = ["meta", "normalized", "redacted"]
    for key in required_keys:
        if key not in data:
            return False, f"Missing required key: {key}"

    # Validate types
    # meta must be dict
    if not isinstance(data["meta"], dict):
        return False, f"meta must be dict, got {type(data['meta']).__name__}"

    # redacted must be str
    if not isinstance(data["redacted"], str):
        return False, f"redacted must be str, got {type(data['redacted']).__name__}"

    # normalized must be None or str
    normalized = data["normalized"]
    if normalized is not None and not isinstance(normalized, str):
        return False, f"normalized must be None or str, got {type(normalized).__name__}"

    # Validate meta.schema_version is "1" (string)
    if data["meta"].get("schema_version") != "1":
        return False, f"meta.schema_version must be '1', got {data['meta'].get('schema_version')!r}"

    return True, None


def main() -> int:
    """
    Main entry point.

    Reads stdin, expects exactly one JSONL line, validates it.

    Returns:
        Exit code (0 = pass, 2 = fail)
    """
    print("=" * 60)
    print("JSONL CONSUMER CHECK: ninobyte-context-cleaner")
    print("=" * 60)
    print()

    # Read all stdin
    stdin_content = sys.stdin.read()

    if not stdin_content.strip():
        print("Error: No input received on stdin")
        print()
        print("-" * 60)
        print("CONSUMER: FAIL")
        return 2

    # Split into lines (filter empty)
    lines = [l for l in stdin_content.strip().split("\n") if l.strip()]

    if len(lines) == 0:
        print("Error: No JSONL lines found")
        print()
        print("-" * 60)
        print("CONSUMER: FAIL")
        return 2

    if len(lines) > 1:
        print(f"Warning: Expected 1 JSONL line, got {len(lines)}. Validating first line only.")
        print()

    # Validate first line
    line = lines[0]
    passed, error = validate_jsonl(line)

    if passed:
        print("[PASS] JSONL line is valid")
        print()
        print("Validated:")
        print("  - Required keys: meta, normalized, redacted")
        print("  - Types: meta=dict, normalized=None|str, redacted=str")
        print("  - Schema version: '1'")
        print()
        print("-" * 60)
        print("CONSUMER: PASS")
        return 0
    else:
        print(f"[FAIL] {error}")
        print()
        print("-" * 60)
        print("CONSUMER: FAIL")
        return 2


if __name__ == "__main__":
    sys.exit(main())
