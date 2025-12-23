#!/usr/bin/env python3
"""ADR Cross-Link Validator.

Enforces bidirectional integrity between:
- docs/adr/ADR-*.md (Architecture Decision Records)
- ops/evidence/decisions/*.canonical.json (decision receipts)

Policies:
1. Every ADR must contain exactly one canonical receipt reference
2. Every decision receipt must be referenced by at least one ADR
3. All receipt paths must exist on disk

Usage:
    python3 scripts/ci/validate_adr_links.py

Exit codes:
    0 - All validations passed
    1 - One or more validations failed
"""

import re
import sys
from pathlib import Path

# Resolve repo root
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
ADR_DIR = REPO_ROOT / "docs" / "adr"
DECISION_RECEIPTS_DIR = REPO_ROOT / "ops" / "evidence" / "decisions"

# Pattern to match receipt references (backticked or plain)
RECEIPT_PATTERN = re.compile(
    r"`?(ops/evidence/decisions/[^`\s]+\.canonical\.json)`?"
)


def log_ok(msg: str) -> None:
    print(f"  \u2705 {msg}")


def log_fail(msg: str) -> None:
    print(f"  \u274c {msg}")


def log_info(msg: str) -> None:
    print(f"  \u2139\ufe0f  {msg}")


def find_adr_files() -> list[Path]:
    """Find all ADR markdown files (excluding README and TEMPLATE)."""
    if not ADR_DIR.exists():
        return []

    return [
        f
        for f in ADR_DIR.glob("ADR-*.md")
        if f.name not in ("README.md", "TEMPLATE.md")
    ]


def find_all_receipts() -> set[str]:
    """Find all canonical.json receipts in the decision evidence directory.

    Returns:
        Set of repo-relative paths to canonical.json files
    """
    if not DECISION_RECEIPTS_DIR.exists():
        return set()

    receipts = set()
    for f in DECISION_RECEIPTS_DIR.glob("*.canonical.json"):
        # Convert to repo-relative path
        rel_path = str(f.relative_to(REPO_ROOT)).replace("\\", "/")
        receipts.add(rel_path)

    return receipts


def extract_receipt_references(adr_path: Path) -> list[str]:
    """Extract all receipt path references from an ADR file.

    Returns:
        List of receipt paths found in the file
    """
    content = adr_path.read_text(encoding="utf-8")
    matches = RECEIPT_PATTERN.findall(content)
    return matches


def validate_adr_receipts(
    adr_files: list[Path],
) -> tuple[dict[str, str], list[str]]:
    """Validate that each ADR has exactly one valid receipt reference.

    Returns:
        Tuple of:
        - Dict mapping ADR filename to its receipt path
        - List of error messages
    """
    adr_to_receipt: dict[str, str] = {}
    errors: list[str] = []

    for adr_path in adr_files:
        receipts = extract_receipt_references(adr_path)

        if len(receipts) == 0:
            errors.append(f"{adr_path.name}: Missing receipt reference")
            continue

        if len(receipts) > 1:
            errors.append(
                f"{adr_path.name}: Multiple receipt references found ({len(receipts)})"
            )
            continue

        receipt_path = receipts[0]

        # Validate path format
        if not receipt_path.startswith("ops/evidence/decisions/"):
            errors.append(
                f"{adr_path.name}: Receipt path must start with "
                f"'ops/evidence/decisions/' (got: '{receipt_path}')"
            )
            continue

        if not receipt_path.endswith(".canonical.json"):
            errors.append(
                f"{adr_path.name}: Receipt path must end with "
                f"'.canonical.json' (got: '{receipt_path}')"
            )
            continue

        # Check file exists
        full_path = REPO_ROOT / receipt_path
        if not full_path.exists():
            errors.append(f"{adr_path.name}: Receipt file not found: {receipt_path}")
            continue

        adr_to_receipt[adr_path.name] = receipt_path

    return adr_to_receipt, errors


def validate_no_orphan_receipts(
    adr_to_receipt: dict[str, str],
    all_receipts: set[str],
) -> list[str]:
    """Validate that all receipts are referenced by at least one ADR.

    Returns:
        List of error messages for unreferenced receipts
    """
    referenced = set(adr_to_receipt.values())
    orphans = all_receipts - referenced
    errors = []

    for orphan in sorted(orphans):
        errors.append(f"Unreferenced decision receipt: {orphan}")

    return errors


def main() -> int:
    """Run ADR cross-link validation."""
    print()
    print("=" * 60)
    print("ADR Cross-Link Validator")
    print("=" * 60)

    all_errors: list[str] = []

    # Step 1: Find ADR files
    print("\n--- Scanning ADR Files ---")
    adr_files = find_adr_files()
    log_info(f"Found {len(adr_files)} ADR file(s)")

    if not adr_files:
        log_info("No ADRs to validate")
        print()
        print("=" * 60)
        print("\n\u2705 PASSED: No ADRs to validate")
        return 0

    # Step 2: Find all receipts on disk
    print("\n--- Scanning Receipt Files ---")
    all_receipts = find_all_receipts()
    log_info(f"Found {len(all_receipts)} canonical receipt file(s)")

    # Step 3: Validate ADR receipt references
    print("\n--- Validating ADR Receipt References ---")
    adr_to_receipt, receipt_errors = validate_adr_receipts(adr_files)
    all_errors.extend(receipt_errors)

    if receipt_errors:
        for err in receipt_errors:
            log_fail(err)
    else:
        log_ok(f"All {len(adr_files)} ADR(s) have valid receipt references")

    # Step 4: Validate no orphan receipts
    print("\n--- Checking for Orphan Receipts ---")
    orphan_errors = validate_no_orphan_receipts(adr_to_receipt, all_receipts)
    all_errors.extend(orphan_errors)

    if orphan_errors:
        for err in orphan_errors:
            log_fail(err)
    else:
        log_ok("No orphan receipts found")

    # Summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"  ADRs checked:           {len(adr_files)}")
    print(f"  ADRs with valid links:  {len(adr_to_receipt)}")
    print(f"  Receipts on disk:       {len(all_receipts)}")
    print(f"  Receipt errors:         {len(receipt_errors)}")
    print(f"  Orphan receipts:        {len(orphan_errors)}")
    print("=" * 60)

    if all_errors:
        print("\n\u274c FAILED: Cross-link validation errors found")
        return 1

    print("\n\u2705 PASSED: All cross-links validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
