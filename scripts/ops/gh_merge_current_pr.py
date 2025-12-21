#!/usr/bin/env python3
"""
Ninobyte PR Merge Guardrail

Safely merges the PR associated with the current branch using GitHub CLI.
Prevents accidental merges on main/master branches.

Usage:
    python scripts/ops/gh_merge_current_pr.py

Behavior:
    1. Detects current git branch
    2. Refuses to run on main/master (guardrail)
    3. Finds PR number for current branch via `gh pr view`
    4. Merges PR with --squash --delete-branch --auto

Requirements:
    - git CLI
    - GitHub CLI (gh) authenticated
    - Branch protection with required checks (--auto waits for checks)

Exit codes:
    0 - Merge initiated successfully (or --auto is waiting)
    1 - Error (on main, no PR, gh failure)
"""

import subprocess
import sys
from typing import Optional, Tuple


def run_command(args: list[str]) -> Tuple[int, str, str]:
    """
    Run a subprocess command without shell=True.

    Returns:
        Tuple of (returncode, stdout, stderr)
    """
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "Command timed out"
    except FileNotFoundError:
        return 1, "", f"Command not found: {args[0]}"


def get_current_branch() -> Optional[str]:
    """Get the current git branch name."""
    code, stdout, stderr = run_command(["git", "branch", "--show-current"])
    if code != 0:
        print(f"Error: Failed to get current branch: {stderr}")
        return None
    return stdout if stdout else None


def get_pr_number() -> Optional[int]:
    """Get PR number for current branch using gh CLI."""
    code, stdout, stderr = run_command([
        "gh", "pr", "view", "--json", "number", "--jq", ".number"
    ])
    if code != 0:
        return None
    try:
        return int(stdout)
    except ValueError:
        return None


def merge_pr(pr_number: int) -> bool:
    """Merge PR with squash, delete branch, and auto-merge."""
    print(f"Merging PR #{pr_number} with --squash --delete-branch --auto...")

    code, stdout, stderr = run_command([
        "gh", "pr", "merge", str(pr_number),
        "--squash",
        "--delete-branch",
        "--auto"
    ])

    if code != 0:
        print(f"Error: Failed to merge PR: {stderr}")
        return False

    if stdout:
        print(stdout)
    if stderr:
        # gh sometimes outputs to stderr even on success
        print(stderr)

    return True


def main() -> int:
    """Main entry point."""
    print("=" * 50)
    print("Ninobyte PR Merge Guardrail")
    print("=" * 50)

    # Step 1: Get current branch
    branch = get_current_branch()
    if not branch:
        print("Error: Could not determine current branch.")
        print("Are you in a git repository?")
        return 1

    print(f"Current branch: {branch}")

    # Step 2: Guardrail - refuse on main/master
    protected_branches = {"main", "master"}
    if branch in protected_branches:
        print()
        print("=" * 50)
        print("GUARDRAIL TRIGGERED")
        print("=" * 50)
        print(f"Error: Refusing to merge on '{branch}' branch.")
        print()
        print("This script is designed to merge feature branch PRs.")
        print("Direct merges to main/master are not allowed.")
        print()
        print("To merge a PR:")
        print("  1. git checkout <feature-branch>")
        print("  2. python scripts/ops/gh_merge_current_pr.py")
        return 1

    # Step 3: Get PR number
    pr_number = get_pr_number()
    if not pr_number:
        print()
        print("No PR found for this branch.")
        print()
        print("To create a PR first, run:")
        print("  gh pr create --fill")
        print()
        print("Then retry this script.")
        return 1

    print(f"Found PR: #{pr_number}")

    # Step 4: Merge PR
    if merge_pr(pr_number):
        print()
        print("=" * 50)
        print("SUCCESS")
        print("=" * 50)
        print("PR merge initiated with --auto flag.")
        print("If branch protection requires checks, merge will wait.")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
