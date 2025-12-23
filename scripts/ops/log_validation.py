#!/usr/bin/env python3
"""Validation Log CLI with canonical receipts.

Provides commands to manage the validation log with immutable evidence receipts.

Usage:
    # Add a new validation entry
    python3 log_validation.py add \\
        --claim "Validator now enforces orphan checksum policy" \\
        --source "repo governance decision" \\
        --status verified \\
        --confidence medium \\
        --tags governance,evidence \\
        --notes "Phase 4B validation log automation" \\
        --verify

    # List recent entries
    python3 log_validation.py list --limit 10

    # Lint the validation log
    python3 log_validation.py lint
"""

import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

# Resolve repo root for reliable path handling
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
EVIDENCE_DIR = REPO_ROOT / "ops" / "evidence" / "validation"
VALIDATION_LOG = REPO_ROOT / "docs" / "canonical" / "VALIDATION_LOG.md"
VALIDATOR_SCRIPT = REPO_ROOT / "scripts" / "ci" / "validate_evidence_integrity.py"

# Valid enum values
VALID_STATUSES = {"verified", "partially_verified", "disputed", "unverified"}
VALID_CONFIDENCES = {"high", "medium", "low"}


def get_git_head() -> str:
    """Get current git HEAD SHA."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git rev-parse failed: {result.stderr.strip()}")
    return result.stdout.strip()


def canonicalize(data: object) -> str:
    """Return canonical JSON string with trailing newline."""
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ) + "\n"


def compute_sha256(content: str) -> str:
    """Compute SHA256 of string content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def generate_receipt_id(timestamp: datetime.datetime, head_sha: str) -> str:
    """Generate deterministic receipt ID."""
    date_str = timestamp.strftime("%Y%m%d_%H%M%S")
    short_sha = head_sha[:7]
    return f"validation_{date_str}_{short_sha}"


def parse_tags(tags_str: str | None) -> list[str]:
    """Parse comma-separated tags into a list."""
    if not tags_str:
        return []
    tags = [t.strip() for t in tags_str.split(",")]
    return [t for t in tags if t]  # Remove empty strings


def truncate(text: str, max_len: int = 120) -> str:
    """Truncate text to max_len chars, adding ellipsis if needed."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def read_validation_log() -> str | None:
    """Read validation log content, or None if it doesn't exist."""
    if not VALIDATION_LOG.exists():
        return None
    return VALIDATION_LOG.read_text(encoding="utf-8")


def create_validation_log_header() -> str:
    """Create the initial validation log content."""
    return """# Validation Log

This log tracks validated claims with immutable evidence receipts.

| Date (UTC) | Claim | Status | Confidence | Source | Receipt |
|---|---|---|---|---|---|
"""


def receipt_exists_in_log(log_content: str, receipt_path: str) -> bool:
    """Check if a receipt is already referenced in the log."""
    return receipt_path in log_content


def append_log_entry(
    timestamp: datetime.datetime,
    claim: str,
    status: str,
    confidence: str,
    source: str,
    receipt_path: str,
) -> None:
    """Append a new entry to the validation log."""
    log_content = read_validation_log()

    if log_content is None:
        log_content = create_validation_log_header()

    # Check for duplicate
    if receipt_exists_in_log(log_content, receipt_path):
        print(f"Entry already exists for receipt: {receipt_path}")
        return

    # Format the new row
    date_str = timestamp.strftime("%Y-%m-%d %H:%M:%SZ")
    claim_display = truncate(claim, 120)
    source_display = truncate(source, 120)

    new_row = f"| {date_str} | {claim_display} | {status} | {confidence} | {source_display} | `{receipt_path}` |\n"

    # Append the row
    updated_content = log_content.rstrip("\n") + "\n" + new_row

    VALIDATION_LOG.parent.mkdir(parents=True, exist_ok=True)
    VALIDATION_LOG.write_text(updated_content, encoding="utf-8")


def write_receipt(
    receipt_id: str,
    timestamp: datetime.datetime,
    claim: str,
    source: str,
    status: str,
    confidence: str,
    tags: list[str],
    notes: str,
    head_sha: str,
) -> tuple[Path, Path, Path, str]:
    """Write raw, canonical, and sha256 receipt files.

    Returns (raw_path, canonical_path, sha256_path, sha256_hash).
    """
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = EVIDENCE_DIR / f"{receipt_id}.json"
    canonical_path = EVIDENCE_DIR / f"{receipt_id}.canonical.json"
    sha256_path = EVIDENCE_DIR / f"{receipt_id}.canonical.json.sha256"

    receipt_data = {
        "schema_version": "1",
        "created_at_utc": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "claim": claim,
        "source": source,
        "status": status,
        "confidence": confidence,
        "tags": tags,
        "notes": notes,
        "actor": "scripts/ops/log_validation.py",
        "repo_head": head_sha,
        "receipt_id": receipt_id,
    }

    # Write raw (pretty-printed)
    raw_content = json.dumps(receipt_data, indent=2, ensure_ascii=False) + "\n"
    raw_path.write_text(raw_content, encoding="utf-8")

    # Write canonical
    canonical_content = canonicalize(receipt_data)
    canonical_path.write_text(canonical_content, encoding="utf-8")

    # Compute and write SHA256 with repo-relative path
    sha256_hash = compute_sha256(canonical_content)
    repo_relative_path = str(canonical_path.relative_to(REPO_ROOT)).replace("\\", "/")
    sha256_line = f"{sha256_hash}  {repo_relative_path}\n"
    sha256_path.write_text(sha256_line, encoding="utf-8")

    return raw_path, canonical_path, sha256_path, sha256_hash


def run_validator() -> bool:
    """Run the evidence integrity validator. Returns True if passed."""
    print()
    print("=" * 60)
    print("Running Evidence Integrity Validator...")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, str(VALIDATOR_SCRIPT)],
        cwd=REPO_ROOT,
        check=False,
    )

    return result.returncode == 0


def cmd_add(args: argparse.Namespace) -> int:
    """Handle the 'add' subcommand."""
    # Validate inputs
    if not args.claim or not args.claim.strip():
        print("Error: --claim is required and must be non-empty.", file=sys.stderr)
        return 1

    if not args.source or not args.source.strip():
        print("Error: --source is required and must be non-empty.", file=sys.stderr)
        return 1

    if args.status not in VALID_STATUSES:
        print(f"Error: --status must be one of: {', '.join(sorted(VALID_STATUSES))}", file=sys.stderr)
        return 1

    if args.confidence not in VALID_CONFIDENCES:
        print(f"Error: --confidence must be one of: {', '.join(sorted(VALID_CONFIDENCES))}", file=sys.stderr)
        return 1

    claim = args.claim.strip()
    source = args.source.strip()
    status = args.status
    confidence = args.confidence
    tags = parse_tags(args.tags)
    notes = args.notes.strip() if args.notes else ""

    # Get git HEAD
    try:
        head_sha = get_git_head()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Generate receipt ID
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    receipt_id = generate_receipt_id(timestamp, head_sha)

    # Repo-relative path for display/log
    receipt_path = f"ops/evidence/validation/{receipt_id}.canonical.json"

    mode_label = "[DRY RUN] " if args.dry_run else ""
    print("=" * 60)
    print(f"{mode_label}Validation Log Entry")
    print("=" * 60)
    print(f"Receipt ID:  {receipt_id}")
    print(f"Timestamp:   {timestamp.strftime('%Y-%m-%d %H:%M:%SZ')}")
    print(f"Claim:       {truncate(claim, 80)}")
    print(f"Source:      {truncate(source, 80)}")
    print(f"Status:      {status}")
    print(f"Confidence:  {confidence}")
    print(f"Tags:        {', '.join(tags) if tags else '(none)'}")
    print(f"Notes:       {truncate(notes, 80) if notes else '(none)'}")
    print(f"Git HEAD:    {head_sha[:12]}")
    print()

    if args.dry_run:
        print("Would write:")
        print(f"  ops/evidence/validation/{receipt_id}.json")
        print(f"  ops/evidence/validation/{receipt_id}.canonical.json")
        print(f"  ops/evidence/validation/{receipt_id}.canonical.json.sha256")
        print(f"  docs/canonical/VALIDATION_LOG.md (append row)")
        print()
        print("=" * 60)
        print("DRY RUN complete. No files were modified.")
        return 0

    # Write receipt files
    raw_path, canonical_path, sha256_path, sha256_hash = write_receipt(
        receipt_id=receipt_id,
        timestamp=timestamp,
        claim=claim,
        source=source,
        status=status,
        confidence=confidence,
        tags=tags,
        notes=notes,
        head_sha=head_sha,
    )

    print("Files created:")
    print(f"  Raw:       {raw_path.relative_to(REPO_ROOT)} ({raw_path.stat().st_size}b)")
    print(f"  Canonical: {canonical_path.relative_to(REPO_ROOT)} ({canonical_path.stat().st_size}b)")
    print(f"  SHA256:    {sha256_path.relative_to(REPO_ROOT)} ({sha256_path.stat().st_size}b)")
    print()
    print(f"SHA256: {sha256_hash}")

    # Append to validation log
    append_log_entry(
        timestamp=timestamp,
        claim=claim,
        status=status,
        confidence=confidence,
        source=source,
        receipt_path=receipt_path,
    )
    print()
    print(f"Log updated: docs/canonical/VALIDATION_LOG.md")
    print("=" * 60)

    # Run verification if requested
    if args.verify:
        if not run_validator():
            print("\n❌ Verification FAILED")
            return 1
        print("\n✅ Verification PASSED")

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """Handle the 'list' subcommand."""
    log_content = read_validation_log()

    if log_content is None:
        print("Validation log not found: docs/canonical/VALIDATION_LOG.md")
        print("Use 'add' command to create the first entry.")
        return 0

    lines = log_content.strip().split("\n")

    # Find table rows (lines starting with |, excluding header and separator)
    table_rows = []
    in_table = False
    for line in lines:
        if line.startswith("|"):
            if "---" in line:
                in_table = True
                continue
            if in_table:
                table_rows.append(line)

    if not table_rows:
        print("No entries found in validation log.")
        return 0

    limit = args.limit if args.limit else 10
    recent = table_rows[-limit:]

    print("=" * 60)
    print(f"Recent Validation Entries (last {len(recent)})")
    print("=" * 60)

    for row in recent:
        # Parse the row
        cols = [c.strip() for c in row.split("|")[1:-1]]
        if len(cols) >= 6:
            date, claim, status, confidence, source, receipt = cols
            print(f"\nDate:       {date}")
            print(f"Claim:      {claim}")
            print(f"Status:     {status}")
            print(f"Confidence: {confidence}")
            print(f"Receipt:    {receipt}")

    print()
    print("=" * 60)
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    """Handle the 'lint' subcommand."""
    log_content = read_validation_log()

    if log_content is None:
        print("Validation log not found: docs/canonical/VALIDATION_LOG.md")
        return 0

    print("=" * 60)
    print("Validation Log Lint")
    print("=" * 60)

    lines = log_content.strip().split("\n")
    errors = []

    # Check for table header
    header_pattern = r"\|\s*Date.*\|\s*Claim.*\|\s*Status.*\|\s*Confidence.*\|\s*Source.*\|\s*Receipt.*\|"
    header_found = False
    separator_found = False

    for i, line in enumerate(lines, 1):
        if re.match(header_pattern, line, re.IGNORECASE):
            header_found = True
            print(f"✅ Line {i}: Table header found")
        elif line.startswith("|") and "---" in line:
            separator_found = True
            print(f"✅ Line {i}: Separator row found")
        elif line.startswith("|"):
            # Count columns
            cols = [c.strip() for c in line.split("|")]
            # Remove empty first and last (from leading/trailing |)
            cols = [c for c in cols if c or cols.index(c) not in [0, len(cols) - 1]]
            actual_cols = len([c for c in line.split("|")[1:-1]])
            if actual_cols != 6:
                errors.append(f"Line {i}: Expected 6 columns, found {actual_cols}")
                print(f"❌ Line {i}: Column count mismatch (expected 6, got {actual_cols})")
            else:
                print(f"✅ Line {i}: Valid row (6 columns)")

    if not header_found:
        errors.append("Table header not found")
        print("❌ Table header not found")

    if not separator_found:
        errors.append("Table separator row not found")
        print("❌ Table separator row not found")

    print()
    print("=" * 60)

    if errors:
        print(f"FAILED: {len(errors)} error(s) found")
        return 1

    print("PASSED: Validation log is well-formed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validation Log CLI with canonical receipts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'add' subcommand
    add_parser = subparsers.add_parser("add", help="Add a new validation entry")
    add_parser.add_argument("--claim", required=True, help="The claim being validated")
    add_parser.add_argument("--source", required=True, help="Source of the claim (URL or citation)")
    add_parser.add_argument(
        "--status",
        required=True,
        choices=sorted(VALID_STATUSES),
        help="Validation status",
    )
    add_parser.add_argument(
        "--confidence",
        required=True,
        choices=sorted(VALID_CONFIDENCES),
        help="Confidence level",
    )
    add_parser.add_argument("--tags", help="Comma-separated tags")
    add_parser.add_argument("--notes", default="", help="Additional notes")
    add_parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    add_parser.add_argument("--verify", action="store_true", help="Run integrity validator after")

    # 'list' subcommand
    list_parser = subparsers.add_parser("list", help="List recent validation entries")
    list_parser.add_argument("--limit", type=int, default=10, help="Number of entries to show")

    # 'lint' subcommand
    subparsers.add_parser("lint", help="Lint the validation log for format errors")

    args = parser.parse_args()

    if args.command == "add":
        return cmd_add(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "lint":
        return cmd_lint(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
