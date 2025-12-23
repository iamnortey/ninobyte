#!/usr/bin/env python3
"""Decision Log CLI with ADR and canonical receipts.

Provides commands to manage Architecture Decision Records with immutable evidence receipts.

Usage:
    # Add a new decision (creates ADR + receipt)
    python3 log_decision.py add \\
        --title "Use canonical JSON for receipts" \\
        --status accepted \\
        --context "We need deterministic hashing" \\
        --decision "Adopt canonical JSON serialization" \\
        --consequences "All receipts use sorted keys" \\
        --tags governance,evidence \\
        --verify

    # Preview without writing
    python3 log_decision.py add \\
        --title "Draft decision" \\
        --status proposed \\
        --context "..." \\
        --decision "..." \\
        --consequences "..." \\
        --dry-run

    # List recent ADRs
    python3 log_decision.py list --limit 10

    # Lint ADR structure
    python3 log_decision.py lint
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
ADR_DIR = REPO_ROOT / "docs" / "adr"
EVIDENCE_DIR = REPO_ROOT / "ops" / "evidence" / "decisions"
VALIDATOR_SCRIPT = REPO_ROOT / "scripts" / "ci" / "validate_evidence_integrity.py"
ADR_LINK_VALIDATOR = REPO_ROOT / "scripts" / "ci" / "validate_adr_links.py"

# Valid enum values
VALID_STATUSES = {"proposed", "accepted", "superseded", "rejected"}


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
    return f"decision_{date_str}_{short_sha}"


def generate_adr_filename(timestamp: datetime.datetime, title: str) -> str:
    """Generate ADR filename from timestamp and title."""
    date_str = timestamp.strftime("%Y%m%d-%H%M%S")
    # Create slug from title
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")[:50]  # Limit length
    return f"ADR-{date_str}-{slug}.md"


def parse_tags(tags_str: str | None) -> list[str]:
    """Parse comma-separated tags into a list."""
    if not tags_str:
        return []
    tags = [t.strip() for t in tags_str.split(",")]
    return [t for t in tags if t]


def truncate(text: str, max_len: int = 120) -> str:
    """Truncate text to max_len chars, adding ellipsis if needed."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def write_receipt(
    receipt_id: str,
    timestamp: datetime.datetime,
    title: str,
    status: str,
    context: str,
    decision: str,
    consequences: str,
    tags: list[str],
    source: str,
    notes: str,
    head_sha: str,
    adr_path: str,
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
        "receipt_id": receipt_id,
        "created_at_utc": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "title": title,
        "status": status,
        "context": context,
        "decision": decision,
        "consequences": consequences,
        "tags": tags,
        "source": source,
        "notes": notes,
        "actor": "scripts/ops/log_decision.py",
        "repo_head": head_sha,
        "adr_path": adr_path,
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


def write_adr(
    adr_filename: str,
    timestamp: datetime.datetime,
    title: str,
    status: str,
    context: str,
    decision: str,
    consequences: str,
    receipt_path: str,
) -> Path:
    """Write ADR markdown file.

    Returns the path to the created file.
    """
    ADR_DIR.mkdir(parents=True, exist_ok=True)

    adr_path = ADR_DIR / adr_filename
    date_str = timestamp.strftime("%Y-%m-%d")

    content = f"""# {adr_filename.replace('.md', '')}: {title}

## Status

**Status**: {status}

**Date**: {date_str}

## Context

{context}

## Decision

{decision}

## Consequences

{consequences}

## Evidence Receipt

**Receipt Path**: `{receipt_path}`

This ADR is anchored to an immutable evidence receipt containing:
- Timestamp: {timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")}
- Git commit SHA (at time of decision)
- Decision metadata
- Cryptographic integrity proof (SHA256)
"""

    adr_path.write_text(content, encoding="utf-8")
    return adr_path


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


def run_adr_link_validator() -> bool:
    """Run the ADR cross-link validator. Returns True if passed."""
    print()
    print("=" * 60)
    print("Running ADR Cross-Link Validator...")
    print("=" * 60)

    if not ADR_LINK_VALIDATOR.exists():
        print(f"ADR link validator not found: {ADR_LINK_VALIDATOR}")
        return False

    result = subprocess.run(
        [sys.executable, str(ADR_LINK_VALIDATOR)],
        cwd=REPO_ROOT,
        check=False,
    )

    return result.returncode == 0


def cmd_add(args: argparse.Namespace) -> int:
    """Handle the 'add' subcommand."""
    # Validate inputs
    if not args.title or not args.title.strip():
        print("Error: --title is required and must be non-empty.", file=sys.stderr)
        return 1

    if args.status not in VALID_STATUSES:
        print(
            f"Error: --status must be one of: {', '.join(sorted(VALID_STATUSES))}",
            file=sys.stderr,
        )
        return 1

    if not args.context or not args.context.strip():
        print("Error: --context is required and must be non-empty.", file=sys.stderr)
        return 1

    if not args.decision or not args.decision.strip():
        print("Error: --decision is required and must be non-empty.", file=sys.stderr)
        return 1

    if not args.consequences or not args.consequences.strip():
        print(
            "Error: --consequences is required and must be non-empty.", file=sys.stderr
        )
        return 1

    title = args.title.strip()
    status = args.status
    context = args.context.strip()
    decision = args.decision.strip()
    consequences = args.consequences.strip()
    tags = parse_tags(args.tags)
    source = args.source.strip() if args.source else ""
    notes = args.notes.strip() if args.notes else ""

    # Get git HEAD
    try:
        head_sha = get_git_head()
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Generate IDs and paths
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    receipt_id = generate_receipt_id(timestamp, head_sha)
    adr_filename = generate_adr_filename(timestamp, title)

    # Repo-relative paths
    receipt_path = f"ops/evidence/decisions/{receipt_id}.canonical.json"
    adr_rel_path = f"docs/adr/{adr_filename}"

    mode_label = "[DRY RUN] " if args.dry_run else ""
    print("=" * 60)
    print(f"{mode_label}Architecture Decision Record")
    print("=" * 60)
    print(f"Receipt ID:    {receipt_id}")
    print(f"ADR File:      {adr_filename}")
    print(f"Timestamp:     {timestamp.strftime('%Y-%m-%d %H:%M:%SZ')}")
    print(f"Title:         {truncate(title, 60)}")
    print(f"Status:        {status}")
    print(f"Context:       {truncate(context, 60)}")
    print(f"Decision:      {truncate(decision, 60)}")
    print(f"Consequences:  {truncate(consequences, 60)}")
    print(f"Tags:          {', '.join(tags) if tags else '(none)'}")
    print(f"Git HEAD:      {head_sha[:12]}")
    print()

    if args.dry_run:
        print("Would write:")
        print(f"  docs/adr/{adr_filename}")
        print(f"  ops/evidence/decisions/{receipt_id}.json")
        print(f"  ops/evidence/decisions/{receipt_id}.canonical.json")
        print(f"  ops/evidence/decisions/{receipt_id}.canonical.json.sha256")
        print()
        print("=" * 60)
        print("DRY RUN complete. No files were modified.")
        return 0

    # Write receipt files
    raw_path, canonical_path, sha256_path, sha256_hash = write_receipt(
        receipt_id=receipt_id,
        timestamp=timestamp,
        title=title,
        status=status,
        context=context,
        decision=decision,
        consequences=consequences,
        tags=tags,
        source=source,
        notes=notes,
        head_sha=head_sha,
        adr_path=adr_rel_path,
    )

    # Write ADR file
    adr_path = write_adr(
        adr_filename=adr_filename,
        timestamp=timestamp,
        title=title,
        status=status,
        context=context,
        decision=decision,
        consequences=consequences,
        receipt_path=receipt_path,
    )

    print("Files created:")
    print(f"  ADR:       {adr_path.relative_to(REPO_ROOT)} ({adr_path.stat().st_size}b)")
    print(f"  Raw:       {raw_path.relative_to(REPO_ROOT)} ({raw_path.stat().st_size}b)")
    print(
        f"  Canonical: {canonical_path.relative_to(REPO_ROOT)} ({canonical_path.stat().st_size}b)"
    )
    print(
        f"  SHA256:    {sha256_path.relative_to(REPO_ROOT)} ({sha256_path.stat().st_size}b)"
    )
    print()
    print(f"SHA256: {sha256_hash}")
    print("=" * 60)

    # Run verification if requested
    if args.verify:
        if not run_validator():
            print("\n\u274c Evidence Integrity: FAILED")
            return 1
        print("\n\u2705 Evidence Integrity: PASSED")

        if not run_adr_link_validator():
            print("\n\u274c ADR Cross-Link: FAILED")
            return 1
        print("\n\u2705 ADR Cross-Link: PASSED")

    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """Handle the 'list' subcommand."""
    if not ADR_DIR.exists():
        print("ADR directory not found: docs/adr/")
        print("Use 'add' command to create the first ADR.")
        return 0

    # Find all ADR files (exclude README and TEMPLATE)
    adr_files = sorted(
        [
            f
            for f in ADR_DIR.glob("ADR-*.md")
            if f.name not in ("README.md", "TEMPLATE.md")
        ],
        reverse=True,
    )

    if not adr_files:
        print("No ADRs found in docs/adr/")
        return 0

    limit = args.limit if args.limit else 10
    recent = adr_files[:limit]

    print("=" * 60)
    print(f"Recent ADRs (showing {len(recent)} of {len(adr_files)})")
    print("=" * 60)

    for adr_path in recent:
        content = adr_path.read_text(encoding="utf-8")

        # Extract title from first heading
        title_match = re.search(r"^# .+?: (.+)$", content, re.MULTILINE)
        title = title_match.group(1) if title_match else "(no title)"

        # Extract status
        status_match = re.search(r"\*\*Status\*\*:\s*(\w+)", content)
        status = status_match.group(1) if status_match else "(unknown)"

        # Extract receipt path
        receipt_match = re.search(
            r"`(ops/evidence/decisions/[^`]+\.canonical\.json)`", content
        )
        receipt = receipt_match.group(1) if receipt_match else "(no receipt)"

        print(f"\n{adr_path.name}")
        print(f"  Title:   {truncate(title, 50)}")
        print(f"  Status:  {status}")
        print(f"  Receipt: {receipt}")

    print()
    print("=" * 60)
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    """Handle the 'lint' subcommand."""
    if not ADR_DIR.exists():
        print("ADR directory not found: docs/adr/")
        return 0

    print("=" * 60)
    print("ADR Lint")
    print("=" * 60)

    adr_files = [
        f
        for f in ADR_DIR.glob("ADR-*.md")
        if f.name not in ("README.md", "TEMPLATE.md")
    ]

    if not adr_files:
        print("No ADRs found to lint.")
        return 0

    errors = []

    for adr_path in sorted(adr_files):
        content = adr_path.read_text(encoding="utf-8")
        file_errors = []

        # Check for required sections
        required_sections = ["## Status", "## Context", "## Decision", "## Consequences", "## Evidence Receipt"]
        for section in required_sections:
            if section not in content:
                file_errors.append(f"Missing section: {section}")

        # Check for receipt link
        receipt_match = re.search(
            r"`(ops/evidence/decisions/[^`]+\.canonical\.json)`", content
        )
        if not receipt_match:
            file_errors.append("Missing evidence receipt path")
        else:
            receipt_path = REPO_ROOT / receipt_match.group(1)
            if not receipt_path.exists():
                file_errors.append(f"Receipt file not found: {receipt_match.group(1)}")

        if file_errors:
            print(f"\n\u274c {adr_path.name}")
            for err in file_errors:
                print(f"    - {err}")
            errors.extend(file_errors)
        else:
            print(f"\u2705 {adr_path.name}")

    print()
    print("=" * 60)

    if errors:
        print(f"FAILED: {len(errors)} error(s) found")
        return 1

    print(f"PASSED: {len(adr_files)} ADR(s) validated")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Decision Log CLI with ADR and canonical receipts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # 'add' subcommand
    add_parser = subparsers.add_parser("add", help="Add a new ADR with receipt")
    add_parser.add_argument("--title", required=True, help="Decision title")
    add_parser.add_argument(
        "--status",
        required=True,
        choices=sorted(VALID_STATUSES),
        help="Decision status",
    )
    add_parser.add_argument("--context", required=True, help="Context/problem statement")
    add_parser.add_argument("--decision", required=True, help="The decision made")
    add_parser.add_argument("--consequences", required=True, help="Resulting consequences")
    add_parser.add_argument("--tags", help="Comma-separated tags")
    add_parser.add_argument("--source", default="", help="Source reference")
    add_parser.add_argument("--notes", default="", help="Additional notes")
    add_parser.add_argument(
        "--dry-run", action="store_true", help="Preview without writing"
    )
    add_parser.add_argument(
        "--verify", action="store_true", help="Run validators after creation"
    )

    # 'list' subcommand
    list_parser = subparsers.add_parser("list", help="List recent ADRs")
    list_parser.add_argument(
        "--limit", type=int, default=10, help="Number of ADRs to show"
    )

    # 'lint' subcommand
    subparsers.add_parser("lint", help="Lint ADR structure and receipts")

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
