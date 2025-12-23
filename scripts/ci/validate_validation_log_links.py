#!/usr/bin/env python3
"""Validation Log Cross-Link Validator.

Enforces bidirectional integrity between:
- docs/canonical/VALIDATION_LOG.md (log entries)
- ops/evidence/validation/*.canonical.json (evidence receipts)

Policies:
1. Every log entry row with 6 columns MUST reference a valid receipt
2. Every receipt MUST be referenced by at least one log entry
3. Legacy VL-* format entries are exempt from receipt requirement

Usage:
    python3 scripts/ci/validate_validation_log_links.py

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
VALIDATION_LOG = REPO_ROOT / "docs" / "canonical" / "VALIDATION_LOG.md"
VALIDATION_RECEIPTS_DIR = REPO_ROOT / "ops" / "evidence" / "validation"

# Pattern to match receipt references (backticked or plain)
RECEIPT_PATTERN = re.compile(
    r"`?(ops/evidence/validation/[^`\s|]+\.canonical\.json)`?"
)


def log_ok(msg: str) -> None:
    print(f"  \u2705 {msg}")


def log_fail(msg: str) -> None:
    print(f"  \u274c {msg}")


def log_info(msg: str) -> None:
    print(f"  \u2139\ufe0f  {msg}")


def parse_validation_log() -> tuple[list[tuple[int, str, str | None]], list[str]]:
    """Parse VALIDATION_LOG.md and extract table rows.

    Returns:
        Tuple of:
        - List of (line_number, row_type, receipt_path_or_none)
          row_type is 'legacy' for VL-* rows, 'standard' for new format
        - List of all errors found during parsing
    """
    if not VALIDATION_LOG.exists():
        return [], [f"Validation log not found: {VALIDATION_LOG}"]

    content = VALIDATION_LOG.read_text(encoding="utf-8")
    lines = content.split("\n")

    rows: list[tuple[int, str, str | None]] = []
    errors: list[str] = []

    in_table = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip non-table lines
        if not stripped.startswith("|"):
            continue

        # Skip header and separator rows
        if "---" in stripped:
            in_table = True
            continue

        # Skip table headers (before separator)
        if not in_table:
            continue

        # Parse columns
        cols = [c.strip() for c in stripped.split("|")]
        # Remove empty first and last from leading/trailing |
        if cols and cols[0] == "":
            cols = cols[1:]
        if cols and cols[-1] == "":
            cols = cols[:-1]

        # We're looking for 6-column rows in the main validation table
        # But the VALIDATION_LOG has multiple tables, so we need to be careful
        if len(cols) == 6:
            first_col = cols[0]

            # Check if this is a legacy VL-* entry (in older table format)
            # Legacy entries have VL-YYYYMMDD-### in first column
            if re.match(r"VL-\d{8}-\d+", first_col):
                rows.append((i, "legacy", None))
                continue

            # Check if this looks like the new format Date column (YYYY-MM-DD or timestamp)
            # New format: | Date (UTC) | Claim | Status | Confidence | Source | Receipt |
            if re.match(r"\d{4}-\d{2}-\d{2}", first_col):
                # This is a standard new-format row
                receipt_col = cols[5]  # Receipt is the 6th column (index 5)

                # Extract receipt path from the column
                match = RECEIPT_PATTERN.search(receipt_col)
                if match:
                    receipt_path = match.group(1)
                    rows.append((i, "standard", receipt_path))
                else:
                    # Receipt column doesn't have a valid path
                    rows.append((i, "standard", None))
                    errors.append(
                        f"Line {i}: Row missing valid receipt reference "
                        f"(found: '{receipt_col}')"
                    )

        # 4-column rows are the "Pending Validations" table, skip them
        # Other column counts we ignore

    return rows, errors


def find_all_receipts() -> set[str]:
    """Find all canonical.json receipts in the validation evidence directory.

    Returns:
        Set of repo-relative paths to canonical.json files
    """
    if not VALIDATION_RECEIPTS_DIR.exists():
        return set()

    receipts = set()
    for f in VALIDATION_RECEIPTS_DIR.glob("*.canonical.json"):
        # Convert to repo-relative path
        rel_path = str(f.relative_to(REPO_ROOT)).replace("\\", "/")
        receipts.add(rel_path)

    return receipts


def validate_receipts_exist(rows: list[tuple[int, str, str | None]]) -> list[str]:
    """Validate that all referenced receipts exist on disk.

    Returns:
        List of error messages for missing files
    """
    errors = []

    for line_num, row_type, receipt_path in rows:
        if row_type == "legacy" or receipt_path is None:
            continue

        # Validate path format
        if not receipt_path.startswith("ops/evidence/validation/"):
            errors.append(
                f"Line {line_num}: Receipt path must start with "
                f"'ops/evidence/validation/' (got: '{receipt_path}')"
            )
            continue

        if not receipt_path.endswith(".canonical.json"):
            errors.append(
                f"Line {line_num}: Receipt path must end with "
                f"'.canonical.json' (got: '{receipt_path}')"
            )
            continue

        # Check file exists
        full_path = REPO_ROOT / receipt_path
        if not full_path.exists():
            errors.append(
                f"Line {line_num}: Receipt file not found: {receipt_path}"
            )

    return errors


def validate_no_orphan_receipts(
    rows: list[tuple[int, str, str | None]],
    all_receipts: set[str],
) -> list[str]:
    """Validate that all receipts are referenced in the log.

    Returns:
        List of error messages for unreferenced receipts
    """
    # Collect all referenced receipts
    referenced = set()
    for _, row_type, receipt_path in rows:
        if receipt_path:
            referenced.add(receipt_path)

    # Find orphans
    orphans = all_receipts - referenced
    errors = []

    for orphan in sorted(orphans):
        errors.append(f"Unreferenced validation receipt: {orphan}")

    return errors


def main() -> int:
    """Run validation log cross-link validation."""
    print()
    print("=" * 60)
    print("Validation Log Cross-Link Validator")
    print("=" * 60)

    all_errors: list[str] = []

    # Step 1: Parse the validation log
    print("\n--- Parsing Validation Log ---")
    rows, parse_errors = parse_validation_log()
    all_errors.extend(parse_errors)

    legacy_count = sum(1 for _, t, _ in rows if t == "legacy")
    standard_count = sum(1 for _, t, _ in rows if t == "standard")

    log_info(f"Found {len(rows)} table rows ({legacy_count} legacy, {standard_count} standard)")

    # Step 2: Find all receipts on disk
    print("\n--- Scanning Receipt Files ---")
    all_receipts = find_all_receipts()
    log_info(f"Found {len(all_receipts)} canonical receipt file(s)")

    # Step 3: Validate that referenced receipts exist
    print("\n--- Validating Receipt References ---")
    file_errors = validate_receipts_exist(rows)
    all_errors.extend(file_errors)

    if file_errors:
        for err in file_errors:
            log_fail(err)
    else:
        log_ok("All referenced receipts exist")

    # Step 4: Validate no orphan receipts
    print("\n--- Checking for Orphan Receipts ---")
    orphan_errors = validate_no_orphan_receipts(rows, all_receipts)
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
    print(f"  Log rows checked:       {len(rows)}")
    print(f"    Legacy (VL-*):        {legacy_count}")
    print(f"    Standard:             {standard_count}")
    print(f"  Receipts on disk:       {len(all_receipts)}")
    print(f"  Missing receipt rows:   {len(parse_errors)}")
    print(f"  Missing files:          {len(file_errors)}")
    print(f"  Unreferenced receipts:  {len(orphan_errors)}")
    print("=" * 60)

    if all_errors:
        print("\n\u274c FAILED: Cross-link validation errors found")
        return 1

    print("\n\u2705 PASSED: All cross-links validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
