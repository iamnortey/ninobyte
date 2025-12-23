#!/usr/bin/env python3
"""Validate no OS-generated artifacts exist in the repository.

Fails fast if macOS .DS_Store or other OS artifacts are found,
preventing noisy validation failures from filesystem metadata drift.

Usage:
    python3 scripts/ci/validate_no_os_artifacts.py

Exit codes:
    0 - No OS artifacts found
    1 - OS artifacts detected (lists paths and remediation)
"""

import os
import sys
from pathlib import Path
from typing import List, Set

# OS artifact patterns to detect
OS_ARTIFACT_NAMES: Set[str] = {
    ".DS_Store",      # macOS Finder metadata
    "._.DS_Store",    # macOS AppleDouble resource fork
    "Thumbs.db",      # Windows Explorer thumbnails
    "ehthumbs.db",    # Windows Media Center thumbnails
    "Desktop.ini",    # Windows folder settings
}

# Directories to skip during scan
SKIP_DIRS: Set[str] = {
    ".git",
}


def find_os_artifacts(repo_root: Path) -> List[str]:
    """Recursively find OS-generated artifacts in the repo.

    Returns list of repo-relative paths to offending files.
    """
    artifacts = []

    for dirpath, dirnames, filenames in os.walk(repo_root):
        # Skip excluded directories (modify in-place to prevent descent)
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]

        for filename in filenames:
            if filename in OS_ARTIFACT_NAMES:
                full_path = Path(dirpath) / filename
                try:
                    rel_path = full_path.relative_to(repo_root)
                    artifacts.append(str(rel_path))
                except ValueError:
                    artifacts.append(str(full_path))

    return sorted(artifacts)


def main() -> int:
    # Determine repo root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent

    print("=" * 60)
    print("OS Artifact Validator")
    print("=" * 60)

    artifacts = find_os_artifacts(repo_root)

    if artifacts:
        print(f"\n{len(artifacts)} OS artifact(s) detected:\n")
        for artifact in artifacts:
            print(f"  - {artifact}")

        print("\n" + "=" * 60)
        print("Remediation")
        print("=" * 60)
        print("\nRemove all .DS_Store files:")
        print("  find . -name .DS_Store -print -delete")
        print("\nRemove all OS artifacts:")
        print("  find . \\( -name .DS_Store -o -name Thumbs.db -o -name Desktop.ini \\) -print -delete")
        print("\nThese files are ignored by .gitignore but break governance validators.")
        print()

        return 1

    print("\n  No OS artifacts found")
    print("\n" + "=" * 60)
    print("PASSED")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
