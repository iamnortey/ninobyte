#!/usr/bin/env python3
"""One-command evidence contract verification.

Runs the canonical gate sequence for evidence index integrity.
Cross-platform: uses only Python stdlib and existing scripts.

Usage:
    python3 scripts/ops/evidence_contract_check.py

Exit codes:
    0 - All checks pass
    1 - One or more checks failed
"""

import subprocess
import sys
from pathlib import Path


def run_command(args: list, description: str) -> tuple:
    """Run a command and return (success, output)."""
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, f"Timeout after 120s: {description}"
    except Exception as e:
        return False, f"Error: {e}"


def check_index_artifacts(repo_root: Path) -> tuple:
    """Run build_evidence_index.py --check."""
    script = repo_root / "scripts" / "ops" / "build_evidence_index.py"
    success, output = run_command(
        [sys.executable, str(script), "--check"],
        "Index artifacts check",
    )
    return success, output


def check_determinism_tests(repo_root: Path) -> tuple:
    """Run test_evidence_index_determinism.py."""
    script = repo_root / "scripts" / "ops" / "test_evidence_index_determinism.py"
    success, output = run_command(
        [sys.executable, str(script)],
        "Determinism tests",
    )
    # Parse test results from output
    if "Results:" in output:
        for line in output.splitlines():
            if "Results:" in line:
                return success, line.strip()
    return success, "Determinism tests completed" if success else output


def check_print_contract(repo_root: Path) -> tuple:
    """Verify --print output matches INDEX.json byte-for-byte."""
    script = repo_root / "scripts" / "ops" / "build_evidence_index.py"
    index_path = repo_root / "ops" / "evidence" / "INDEX.json"

    # Read expected bytes from INDEX.json
    try:
        expected = index_path.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"Cannot read INDEX.json: {e}"

    # Capture --print output
    try:
        result = subprocess.run(
            [sys.executable, str(script), "--print"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return False, f"--print failed: {result.stderr}"
        actual = result.stdout
    except Exception as e:
        return False, f"Cannot run --print: {e}"

    # Byte-for-byte comparison
    if actual == expected:
        return True, f"Matched ({len(expected)} bytes)"
    else:
        # Find first diff
        for i, (a, b) in enumerate(zip(actual, expected)):
            if a != b:
                return False, f"Diff at byte {i}: expected {repr(b)}, got {repr(a)}"
        if len(actual) != len(expected):
            return False, f"Length mismatch: expected {len(expected)}, got {len(actual)}"
        return False, "Unknown diff"


def main() -> int:
    print("=" * 60)
    print("Evidence Contract Check")
    print("=" * 60)
    print()

    # Determine repo root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent

    checks = [
        ("Index Artifacts", lambda: check_index_artifacts(repo_root)),
        ("Determinism Tests", lambda: check_determinism_tests(repo_root)),
        ("Print Contract", lambda: check_print_contract(repo_root)),
    ]

    all_passed = True
    results = []

    for i, (name, check_fn) in enumerate(checks, 1):
        success, detail = check_fn()
        status = "PASS" if success else "FAIL"
        icon = "\u2705" if success else "\u274c"
        results.append((name, success, detail))
        print(f"[{i}/{len(checks)}] {name + ':':<20} {icon} {status}")
        if not success:
            all_passed = False
            # Show detail on failure
            if detail:
                for line in detail.splitlines()[:5]:
                    print(f"     {line}")

    print()
    print("=" * 60)
    if all_passed:
        print("\u2705 All evidence contracts verified")
    else:
        print("\u274c Evidence contract check FAILED")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
