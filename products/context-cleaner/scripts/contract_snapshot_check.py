#!/usr/bin/env python3
"""
Contract snapshot checker for ninobyte-context-cleaner.

Validates that pinned input produces exact expected output.
Uses in-process CLI invocation (no subprocess) for speed and reliability.

Security:
- No networking imports
- No file writes (read-only validation)
- Stdlib only

Exit Codes:
    0   CONTRACT: PASS
    1   CONTRACT: FAIL

Usage:
    PYTHONPATH=products/context-cleaner/src python products/context-cleaner/scripts/contract_snapshot_check.py
"""

import io
import json
import os
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Path Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
PRODUCT_ROOT = SCRIPT_DIR.parent
TESTS_DIR = PRODUCT_ROOT / "tests"
GOLDENS_DIR = TESTS_DIR / "goldens"

CONTRACT_INPUT = GOLDENS_DIR / "contract_snapshot_input.txt"
CONTRACT_EXPECTED = GOLDENS_DIR / "contract_snapshot_expected.jsonl"


# ---------------------------------------------------------------------------
# In-Process CLI Invocation
# ---------------------------------------------------------------------------

def capture_cli(args: list, stdin_text: str = "") -> tuple:
    """
    Run the CLI main() with captured stdout/stderr.

    Uses argv injection and stream redirection to avoid subprocess.

    Args:
        args: CLI arguments (without the program name)
        stdin_text: Text to provide as stdin

    Returns:
        (stdout, stderr, exit_code)
    """
    from ninobyte_context_cleaner.__main__ import main

    orig_argv = sys.argv
    orig_stdin = sys.stdin
    orig_stdout = sys.stdout
    orig_stderr = sys.stderr

    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    fake_stdin = io.StringIO(stdin_text)

    exit_code = 0

    try:
        sys.argv = ["ninobyte-context-cleaner"] + args
        sys.stdin = fake_stdin
        sys.stdout = captured_stdout
        sys.stderr = captured_stderr

        exit_code = main()
    except SystemExit as e:
        exit_code = e.code if e.code is not None else 0
    finally:
        sys.argv = orig_argv
        sys.stdin = orig_stdin
        sys.stdout = orig_stdout
        sys.stderr = orig_stderr

    return captured_stdout.getvalue(), captured_stderr.getvalue(), exit_code


# ---------------------------------------------------------------------------
# Contract Validation
# ---------------------------------------------------------------------------

def check_contract_snapshot() -> bool:
    """
    Check that pinned input produces exact expected output.

    Returns:
        True if contract is satisfied, False otherwise.
    """
    print("=" * 60)
    print("CONTRACT SNAPSHOT CHECK: ninobyte-context-cleaner")
    print("=" * 60)
    print()

    # Verify golden files exist
    if not CONTRACT_INPUT.exists():
        print(f"[FAIL] Missing input file: {CONTRACT_INPUT}")
        return False

    if not CONTRACT_EXPECTED.exists():
        print(f"[FAIL] Missing expected file: {CONTRACT_EXPECTED}")
        return False

    print(f"Input:    {CONTRACT_INPUT.name}")
    print(f"Expected: {CONTRACT_EXPECTED.name}")
    print()

    # Read golden files
    input_text = CONTRACT_INPUT.read_text(encoding="utf-8")
    expected_output = CONTRACT_EXPECTED.read_text(encoding="utf-8")

    # Run CLI with JSONL output
    stdout, stderr, code = capture_cli(
        ["--output-format", "jsonl"],
        stdin_text=input_text
    )

    if code != 0:
        print(f"[FAIL] CLI exited with code {code}")
        print(f"Stderr: {stderr}")
        return False

    # Compare outputs
    actual_output = stdout

    if actual_output == expected_output:
        print("[PASS] Output matches expected exactly")
        print()
        print("-" * 60)
        print("CONTRACT: PASS")
        return True

    # Detailed failure analysis
    print("[FAIL] Output mismatch")
    print()

    # Try to show structured diff
    try:
        expected_data = json.loads(expected_output.strip())
        actual_data = json.loads(actual_output.strip())

        print("Expected JSON:")
        print(json.dumps(expected_data, indent=2))
        print()
        print("Actual JSON:")
        print(json.dumps(actual_data, indent=2))
        print()

        # Check specific fields
        for key in ["meta", "normalized", "redacted"]:
            if expected_data.get(key) != actual_data.get(key):
                print(f"Mismatch in '{key}':")
                print(f"  Expected: {expected_data.get(key)!r}")
                print(f"  Actual:   {actual_data.get(key)!r}")

    except json.JSONDecodeError:
        print("Expected (raw):")
        print(expected_output[:500])
        print()
        print("Actual (raw):")
        print(actual_output[:500])

    print()
    print("-" * 60)
    print("CONTRACT: FAIL")
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    success = check_contract_snapshot()
    sys.exit(0 if success else 1)
