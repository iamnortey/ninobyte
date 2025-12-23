#!/usr/bin/env python3
"""Validate integrity of canonical evidence files.

Performs two categories of checks:

1. Canonical Validation (existing):
   - Find all *.canonical.json files under ops/evidence/
   - For each, verify sibling .sha256 file exists
   - Verify stored hash matches computed SHA256
   - Verify stored path matches actual repo-relative path

2. Orphan Check (new):
   - Find all *.sha256 files under ops/evidence/
   - For each, verify the referenced target file exists
   - Orphan = checksum file pointing to non-existent target

Usage:
    python scripts/ci/validate_evidence_integrity.py

Exit codes:
    0 - All checks passed
    1 - One or more checks failed (integrity or orphan)
"""

import hashlib
import sys
from pathlib import Path

EVIDENCE_ROOT = Path("ops/evidence")


def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of file contents."""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def parse_sha256_file(sha256_path: Path) -> tuple[str, str]:
    """Parse .sha256 file and return (hash, path).

    Expected format: "<hash>  <repo-relative-path>"
    (two spaces between hash and path)
    """
    content = sha256_path.read_text().strip()
    if "  " not in content:
        raise ValueError(f"Invalid format: expected '<hash>  <path>', got: {content}")
    parts = content.split("  ", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid format: expected '<hash>  <path>', got: {content}")
    return parts[0], parts[1]


def validate_evidence_file(canonical_path: Path) -> list[str]:
    """Validate a single canonical.json file. Returns list of errors."""
    errors = []
    sha256_path = canonical_path.with_suffix(".json.sha256")

    # Convert to repo-relative path (forward slashes for portability)
    repo_relative = str(canonical_path).replace("\\", "/")

    # Check 1: .sha256 file exists
    if not sha256_path.exists():
        errors.append(f"Missing checksum file: {sha256_path}")
        return errors

    # Check 2: Parse .sha256 file
    try:
        stored_hash, stored_path = parse_sha256_file(sha256_path)
    except ValueError as e:
        errors.append(f"Invalid checksum file {sha256_path}: {e}")
        return errors

    # Check 3: Compute actual hash
    try:
        actual_hash = compute_sha256(canonical_path)
    except OSError as e:
        errors.append(f"Cannot read {canonical_path}: {e}")
        return errors

    # Check 4: Compare hashes
    if stored_hash != actual_hash:
        errors.append(
            f"Hash mismatch for {canonical_path}:\n"
            f"  Stored:   {stored_hash}\n"
            f"  Computed: {actual_hash}"
        )

    # Check 5: Compare paths (allow both basename and repo-relative)
    # The stored path can be either just the filename or the full repo-relative path
    expected_paths = [canonical_path.name, repo_relative]
    if stored_path not in expected_paths:
        errors.append(
            f"Path mismatch in {sha256_path}:\n"
            f"  Stored: {stored_path}\n"
            f"  Expected one of: {expected_paths}"
        )

    return errors


def check_for_orphans() -> list[str]:
    """Find orphan .sha256 files whose targets don't exist.

    Returns list of orphan error messages.
    """
    orphans = []

    if not EVIDENCE_ROOT.exists():
        return orphans

    # Find all .sha256 files
    sha256_files = list(EVIDENCE_ROOT.rglob("*.sha256"))

    for sha256_path in sha256_files:
        try:
            _, stored_path = parse_sha256_file(sha256_path)
        except ValueError:
            # Invalid format - will be caught by canonical validation
            continue

        # Check if target exists (stored_path is repo-relative)
        target_path = Path(stored_path)

        # Handle both repo-relative and basename-only paths
        if not target_path.is_absolute():
            # Repo-relative path
            if not target_path.exists():
                # Try as basename in same directory
                basename_path = sha256_path.parent / target_path.name
                if not basename_path.exists():
                    orphans.append(
                        f"Orphan checksum found: {sha256_path} -> {stored_path}"
                    )

    return orphans


def main() -> int:
    print("=" * 60)
    print("Evidence Integrity Validator")
    print("=" * 60)

    if not EVIDENCE_ROOT.exists():
        print(f"Evidence directory not found: {EVIDENCE_ROOT}")
        print("No evidence files to validate.")
        print("=" * 60)
        return 0

    all_errors = []
    orphan_errors = []

    # === Phase 1: Canonical Validation ===
    print("\n--- Canonical File Validation ---")

    canonical_files = list(EVIDENCE_ROOT.rglob("*.canonical.json"))

    if not canonical_files:
        print(f"No *.canonical.json files found in {EVIDENCE_ROOT}")
    else:
        print(f"Found {len(canonical_files)} canonical evidence file(s)\n")

        passed = 0
        failed = 0

        for canonical_path in sorted(canonical_files):
            print(f"Checking: {canonical_path}")
            errors = validate_evidence_file(canonical_path)

            if errors:
                failed += 1
                for error in errors:
                    print(f"  ❌ {error}")
                    all_errors.append(error)
            else:
                passed += 1
                print(f"  ✅ Integrity verified")

        print(f"\nCanonical validation: {passed} passed, {failed} failed")

    # === Phase 2: Orphan Check ===
    print("\n--- Orphan Checksum Detection ---")

    orphan_errors = check_for_orphans()

    if orphan_errors:
        print(f"Found {len(orphan_errors)} orphan checksum file(s):\n")
        for orphan in orphan_errors:
            print(f"  ❌ {orphan}")
    else:
        sha256_count = len(list(EVIDENCE_ROOT.rglob("*.sha256")))
        print(f"✅ No orphans found ({sha256_count} checksum file(s) validated)")

    # === Summary ===
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    total_canonical = len(canonical_files) if canonical_files else 0
    total_errors = len(all_errors) + len(orphan_errors)

    print(f"  Canonical files validated: {total_canonical}")
    print(f"  Integrity errors:          {len(all_errors)}")
    print(f"  Orphan checksums:          {len(orphan_errors)}")
    print("=" * 60)

    if total_errors > 0:
        print("\nFAILED: Evidence integrity check found errors.")
        return 1

    print("\nPASSED: All evidence files verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
