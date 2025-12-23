#!/usr/bin/env python3
"""Capture PR merge receipt as immutable evidence with canonical hashing.

Creates (idempotent - safe to run multiple times):
- Raw receipt: ops/evidence/pr/pr_<N>_merge_receipt.json
- Canonical receipt: ops/evidence/pr/pr_<N>_merge_receipt.canonical.json
- SHA256 checksum: ops/evidence/pr/pr_<N>_merge_receipt.canonical.json.sha256

The checksum file uses repo-relative paths for portability.

Usage:
    python3 capture_pr_merge_receipt.py --pr 43
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

EVIDENCE_DIR = Path("ops/evidence/pr")
GH_JSON_FIELDS = "number,state,mergedAt,mergeCommit,url,title,headRefName,baseRefName"


def check_gh_installed() -> bool:
    """Check if gh CLI is available."""
    return shutil.which("gh") is not None


def fetch_pr_data(pr_number: int) -> dict:
    """Fetch PR data via gh CLI."""
    cmd = [
        "gh", "pr", "view", str(pr_number),
        "--json", GH_JSON_FIELDS,
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh pr view failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture PR merge receipt as immutable evidence.",
    )
    parser.add_argument(
        "--pr",
        type=int,
        required=True,
        help="PR number to capture",
    )
    args = parser.parse_args()

    pr_number = args.pr

    # Pre-flight: check gh CLI
    if not check_gh_installed():
        print("Error: gh CLI not found. Install from https://cli.github.com/", file=sys.stderr)
        return 1

    # Fetch PR data
    print(f"Fetching PR #{pr_number} data...")
    try:
        pr_data = fetch_pr_data(pr_number)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON from gh CLI: {e}", file=sys.stderr)
        return 1

    # Validate PR is merged
    state = pr_data.get("state", "")
    if state != "MERGED":
        print(f"Error: PR #{pr_number} is not merged (state: {state})", file=sys.stderr)
        print("Only merged PRs can have merge receipts.", file=sys.stderr)
        return 1

    # Ensure evidence directory exists
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    # Define file paths
    raw_path = EVIDENCE_DIR / f"pr_{pr_number}_merge_receipt.json"
    canonical_path = EVIDENCE_DIR / f"pr_{pr_number}_merge_receipt.canonical.json"
    sha256_path = EVIDENCE_DIR / f"pr_{pr_number}_merge_receipt.canonical.json.sha256"

    # Write raw receipt (pretty-printed for human readability)
    raw_content = json.dumps(pr_data, indent=2, ensure_ascii=False) + "\n"
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(raw_content)

    # Write canonical receipt
    canonical_content = canonicalize(pr_data)
    with open(canonical_path, "w", encoding="utf-8") as f:
        f.write(canonical_content)

    # Compute and write SHA256 with repo-relative path for portability
    sha256_hash = compute_sha256(canonical_content)
    # Use forward slashes for cross-platform compatibility
    repo_relative_path = str(canonical_path).replace("\\", "/")
    sha256_line = f"{sha256_hash}  {repo_relative_path}\n"
    with open(sha256_path, "w", encoding="utf-8") as f:
        f.write(sha256_line)

    # Print summary
    print()
    print("=" * 60)
    print("PR Merge Receipt Captured")
    print("=" * 60)
    print(f"PR Number:       #{pr_number}")
    print(f"PR Title:        {pr_data.get('title', 'N/A')}")
    print(f"Merged At:       {pr_data.get('mergedAt', 'N/A')}")
    print(f"Merge Commit:    {pr_data.get('mergeCommit', {}).get('oid', 'N/A')}")
    print()
    print("Files created:")
    print(f"  Raw receipt:      {raw_path} ({raw_path.stat().st_size} bytes)")
    print(f"  Canonical:        {canonical_path} ({canonical_path.stat().st_size} bytes)")
    print(f"  SHA256 checksum:  {sha256_path} ({sha256_path.stat().st_size} bytes)")
    print()
    print(f"SHA256: {sha256_hash}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
