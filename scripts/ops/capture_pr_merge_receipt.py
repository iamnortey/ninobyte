#!/usr/bin/env python3
"""Capture PR merge receipt as immutable evidence with canonical hashing.

Creates (idempotent - safe to run multiple times):
- Raw receipt: ops/evidence/pr/pr_<N>_merge_receipt.json
- Canonical receipt: ops/evidence/pr/pr_<N>_merge_receipt.canonical.json
- SHA256 checksum: ops/evidence/pr/pr_<N>_merge_receipt.canonical.json.sha256

The checksum file uses repo-relative paths for portability.

Usage:
    # Single PR (legacy --pr flag still supported)
    python3 capture_pr_merge_receipt.py --pr 43
    python3 capture_pr_merge_receipt.py 43

    # Batch mode (multiple PRs)
    python3 capture_pr_merge_receipt.py 42 44 45 46

    # No args: attempt to detect current branch PR
    python3 capture_pr_merge_receipt.py
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


def get_current_branch_pr() -> int | None:
    """Try to get PR number for current branch."""
    cmd = ["gh", "pr", "view", "--json", "number"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return None
    try:
        data = json.loads(result.stdout)
        return data.get("number")
    except json.JSONDecodeError:
        return None


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
    """Return canonical JSON string with trailing newline.

    Canonical format:
    - Keys sorted recursively
    - Compact separators (no extra whitespace)
    - Unicode preserved (no ASCII escaping)
    - Single trailing newline
    """
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ) + "\n"


def compute_sha256(content: str) -> str:
    """Compute SHA256 of string content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def capture_pr_receipt(pr_number: int) -> tuple[bool, str]:
    """Capture a single PR's merge receipt.

    Returns (success: bool, message: str).
    """
    # Fetch PR data
    try:
        pr_data = fetch_pr_data(pr_number)
    except RuntimeError as e:
        return False, f"PR #{pr_number}: {e}"
    except json.JSONDecodeError as e:
        return False, f"PR #{pr_number}: Invalid JSON from gh CLI: {e}"

    # Validate PR is merged
    state = pr_data.get("state", "")
    if state != "MERGED":
        return False, f"PR #{pr_number}: Not merged (state: {state})"

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

    # Build summary
    title = pr_data.get("title", "N/A")
    merged_at = pr_data.get("mergedAt", "N/A")
    merge_commit = pr_data.get("mergeCommit", {}).get("oid", "N/A")[:12]

    summary = (
        f"PR #{pr_number}: {title}\n"
        f"  Merged:    {merged_at}\n"
        f"  Commit:    {merge_commit}\n"
        f"  SHA256:    {sha256_hash}\n"
        f"  Files:     {raw_path.stat().st_size}b / {canonical_path.stat().st_size}b / {sha256_path.stat().st_size}b"
    )

    return True, summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Capture PR merge receipt as immutable evidence.",
        epilog="Examples:\n"
               "  capture_pr_merge_receipt.py 43          # Single PR\n"
               "  capture_pr_merge_receipt.py 42 44 45    # Batch mode\n"
               "  capture_pr_merge_receipt.py --pr 43     # Legacy flag\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "pr_numbers",
        type=int,
        nargs="*",
        metavar="PR",
        help="PR number(s) to capture (positional)",
    )
    parser.add_argument(
        "--pr",
        type=int,
        dest="legacy_pr",
        help="PR number (legacy flag, prefer positional args)",
    )
    args = parser.parse_args()

    # Collect PR numbers from all sources
    pr_numbers: list[int] = []

    if args.pr_numbers:
        pr_numbers.extend(args.pr_numbers)

    if args.legacy_pr:
        if args.legacy_pr not in pr_numbers:
            pr_numbers.append(args.legacy_pr)

    # If no PRs specified, try current branch
    if not pr_numbers:
        current_pr = get_current_branch_pr()
        if current_pr:
            pr_numbers.append(current_pr)
            print(f"Auto-detected current branch PR: #{current_pr}")
        else:
            print("Error: No PR numbers specified and no PR found for current branch.", file=sys.stderr)
            print("Usage: capture_pr_merge_receipt.py <PR_NUMBER> [PR_NUMBER ...]", file=sys.stderr)
            return 1

    # Pre-flight: check gh CLI
    if not check_gh_installed():
        print("Error: gh CLI not found. Install from https://cli.github.com/", file=sys.stderr)
        return 1

    # Process each PR
    print("=" * 60)
    print("PR Merge Receipt Capture")
    print("=" * 60)
    print(f"Processing {len(pr_numbers)} PR(s): {', '.join(f'#{n}' for n in pr_numbers)}")
    print()

    successes = []
    failures = []

    for pr_number in pr_numbers:
        print(f"Fetching PR #{pr_number}...")
        success, message = capture_pr_receipt(pr_number)
        if success:
            successes.append((pr_number, message))
            print(f"  ✅ Captured")
        else:
            failures.append((pr_number, message))
            print(f"  ❌ Failed: {message}")

    # Print summary
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    if successes:
        print(f"\n✅ Captured ({len(successes)}):")
        for pr_number, message in successes:
            print()
            print(message)

    if failures:
        print(f"\n❌ Failed ({len(failures)}):")
        for pr_number, message in failures:
            print(f"  {message}")

    print()
    print("=" * 60)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
