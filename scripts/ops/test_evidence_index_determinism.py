#!/usr/bin/env python3
"""Contract-grade regression tests for evidence index determinism.

Tests:
1. Build twice with no changes -> byte-for-byte identical
2. Ordering is strictly (kind, id, path)
3. No generated_at_utc in output (determinism contract v0.6.0)

Usage:
    python3 scripts/ops/test_evidence_index_determinism.py

Exit codes:
    0 - All tests pass
    1 - Test failure
"""

import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from build_evidence_index import build_index, canonicalize, format_human_readable


def test_idempotent_build() -> bool:
    """Build index twice and assert byte-for-byte equality."""
    print("Test: Idempotent build (two runs identical)")

    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent

    # Build twice
    index1, errors1 = build_index(repo_root)
    index2, errors2 = build_index(repo_root)

    if errors1 or errors2:
        print(f"  ❌ FAIL: Errors during build")
        print(f"     Run 1 errors: {errors1}")
        print(f"     Run 2 errors: {errors2}")
        return False

    canonical1 = canonicalize(index1)
    canonical2 = canonicalize(index2)

    if canonical1 != canonical2:
        print("  ❌ FAIL: Canonical outputs differ between runs")
        return False

    human1 = format_human_readable(index1)
    human2 = format_human_readable(index2)

    if human1 != human2:
        print("  ❌ FAIL: Human-readable outputs differ between runs")
        return False

    print("  ✅ PASS: Both runs produce identical output")
    return True


def test_ordering_by_kind_id_path() -> bool:
    """Assert ordering is strictly non-decreasing by (kind, id, path)."""
    print("Test: Ordering by (kind, id, canonical_path)")

    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent

    index_data, errors = build_index(repo_root)

    if errors:
        print(f"  ❌ FAIL: Errors during build: {errors}")
        return False

    items = index_data.get("items", [])

    if len(items) < 2:
        print("  ⚠️  SKIP: Not enough items to verify ordering")
        return True

    for i in range(len(items) - 1):
        curr = items[i]
        next_item = items[i + 1]

        curr_key = (curr["kind"], curr["id"], curr["canonical_path"])
        next_key = (next_item["kind"], next_item["id"], next_item["canonical_path"])

        if curr_key > next_key:
            print(f"  ❌ FAIL: Ordering violation at index {i}")
            print(f"     {curr_key} > {next_key}")
            return False

    print(f"  ✅ PASS: {len(items)} items in correct (kind, id, path) order")
    return True


def test_no_generated_at_utc() -> bool:
    """Assert no generated_at_utc in index output."""
    print("Test: No generated_at_utc in output (determinism contract)")

    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent

    index_data, errors = build_index(repo_root)

    if errors:
        print(f"  ❌ FAIL: Errors during build: {errors}")
        return False

    if "generated_at_utc" in index_data:
        print("  ❌ FAIL: generated_at_utc found in index data")
        return False

    # Also check canonical output
    canonical = canonicalize(index_data)
    if "generated_at" in canonical:
        print("  ❌ FAIL: 'generated_at' found in canonical output")
        return False

    print("  ✅ PASS: No timestamp pollution in index")
    return True


def test_counts_match_items() -> bool:
    """Assert counts dict matches actual item counts by kind."""
    print("Test: Counts match item counts")

    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent

    index_data, errors = build_index(repo_root)

    if errors:
        print(f"  ❌ FAIL: Errors during build: {errors}")
        return False

    counts = index_data.get("counts", {})
    items = index_data.get("items", [])

    # Count items by kind
    actual_counts = {}
    for item in items:
        kind = item["kind"]
        actual_counts[kind] = actual_counts.get(kind, 0) + 1

    if counts != actual_counts:
        print(f"  ❌ FAIL: Counts mismatch")
        print(f"     Declared: {counts}")
        print(f"     Actual:   {actual_counts}")
        return False

    print(f"  ✅ PASS: Counts verified ({sum(counts.values())} total)")
    return True


def main() -> int:
    print("=" * 60)
    print("Evidence Index Determinism Tests")
    print("=" * 60)
    print()

    tests = [
        test_idempotent_build,
        test_ordering_by_kind_id_path,
        test_no_generated_at_utc,
        test_counts_match_items,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  ❌ FAIL: Exception: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
