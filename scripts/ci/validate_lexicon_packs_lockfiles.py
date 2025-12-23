#!/usr/bin/env python3
"""
Lexicon Packs Lockfile Validator

Validates that all lexicon packs have valid, up-to-date lockfiles.

Uses pack discovery API to find all packs dynamically.

Usage:
    python scripts/ci/validate_lexicon_packs_lockfiles.py

Exit codes:
    0 - All lockfiles valid and up-to-date
    1 - Lockfile missing, invalid, or out of sync
"""

import sys
from pathlib import Path


def log_ok(msg: str) -> None:
    print(f"  {msg}")


def log_fail(msg: str) -> None:
    print(f"  {msg}")


def main() -> int:
    """Validate all lexicon pack lockfiles using discovery API."""
    # Determine repo root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent

    # Add lexicon-packs src to path
    lexicon_packs_src = repo_root / "products" / "lexicon-packs" / "src"
    sys.path.insert(0, str(lexicon_packs_src))

    from lexicon_packs.discover import (
        discover_packs,
        verify_all_packs,
        DiscoveryError,
    )
    from lexicon_packs.lockfile import (
        generate_lockfile,
        format_lockfile_json,
        load_lockfile,
        LockfileError,
    )

    packs_root = repo_root / "products" / "lexicon-packs" / "packs"

    if not packs_root.exists():
        print("Lexicon packs directory not found (skipping)")
        return 0

    # Use discovery API to find all packs
    try:
        pack_dirs = discover_packs(packs_root)
    except DiscoveryError as e:
        print(f"Discovery failed: {e}")
        return 1

    if not pack_dirs:
        print("No lexicon packs found (skipping)")
        return 0

    all_passed = True
    validated_count = 0
    failed_count = 0

    for pack_dir in pack_dirs:
        pack_name = pack_dir.name
        lockfile_path = pack_dir / "pack.lock.json"

        # Check lockfile exists
        if not lockfile_path.exists():
            log_fail(f"{pack_name}: pack.lock.json missing")
            print(f"      Run: python -m lexicon_packs lock --pack {pack_dir} --write")
            all_passed = False
            failed_count += 1
            continue

        # Load existing lockfile
        try:
            existing = load_lockfile(pack_dir)
        except LockfileError as e:
            log_fail(f"{pack_name}: Invalid lockfile - {e}")
            all_passed = False
            failed_count += 1
            continue

        # Generate fresh lockfile (using existing timestamp for comparison)
        try:
            fresh = generate_lockfile(
                pack_dir,
                fixed_time=existing["generated_at_utc"]
            )
        except LockfileError as e:
            log_fail(f"{pack_name}: Cannot generate lockfile - {e}")
            all_passed = False
            failed_count += 1
            continue

        # Compare canonical JSON
        existing_json = format_lockfile_json(existing)
        fresh_json = format_lockfile_json(fresh)

        if existing_json != fresh_json:
            log_fail(f"{pack_name}: Lockfile drift detected")

            # Show specific diffs
            for key in fresh:
                if existing.get(key) != fresh.get(key):
                    print(f"      {key}: lockfile has '{existing.get(key)}', computed '{fresh.get(key)}'")

            print(f"      Regenerate: python -m lexicon_packs lock --pack {pack_dir} --write")
            all_passed = False
            failed_count += 1
            continue

        log_ok(f"{pack_name}: lockfile valid")
        validated_count += 1

    # Summary
    print()
    if all_passed:
        print(f"Lexicon packs: {validated_count} lockfile(s) validated")
        return 0
    else:
        print(f"Lexicon packs: {failed_count} lockfile(s) failed, {validated_count} passed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
