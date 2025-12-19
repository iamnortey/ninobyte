#!/usr/bin/env python3
"""
Ninobyte Plugin Skill Sync Tool

Synchronizes the canonical skill source to plugin-bundled copies.
Supports --check mode for CI (exit non-zero on drift) and --sync mode for remediation.

Usage:
    python scripts/ops/sync_plugin_skills.py --check   # CI mode: detect drift, fail if found
    python scripts/ops/sync_plugin_skills.py --sync    # Dev mode: copy canonical → plugin

Version is derived dynamically from canonical SKILL.md frontmatter.
"""

import argparse
import filecmp
import os
import re
import shutil
import sys
from pathlib import Path
from typing import List, Tuple


def get_repo_root() -> Path:
    """Get repository root from script location."""
    script_path = Path(__file__).resolve()
    return script_path.parent.parent.parent


def get_canonical_version(canonical_skill_path: Path) -> str:
    """Extract version from canonical SKILL.md frontmatter or body."""
    skill_md = canonical_skill_path / 'SKILL.md'
    if not skill_md.exists():
        return 'unknown'

    try:
        with open(skill_md, 'r', encoding='utf-8') as f:
            content = f.read()

        # Try to find version in body (e.g., **Version**: 0.1.2)
        match = re.search(r'\*\*Version\*\*:\s*(\d+\.\d+\.\d+)', content)
        if match:
            return match.group(1)

        return 'unknown'
    except Exception:
        return 'unknown'


def log_info(msg: str) -> None:
    print(f"ℹ️  {msg}")


def log_ok(msg: str) -> None:
    print(f"✅ {msg}")


def log_fail(msg: str) -> None:
    print(f"❌ {msg}")


def log_warn(msg: str) -> None:
    print(f"⚠️  {msg}")


def compare_directories(canonical: Path, plugin: Path) -> Tuple[List[str], List[str], List[str]]:
    """
    Compare canonical skill directory to plugin-bundled copy.

    Returns:
        Tuple of (missing_in_plugin, extra_in_plugin, differing_files)
    """
    missing_in_plugin: List[str] = []
    extra_in_plugin: List[str] = []
    differing_files: List[str] = []

    # Get all files in canonical (relative paths)
    canonical_files = set()
    for root, _, files in os.walk(canonical):
        for f in files:
            rel_path = os.path.relpath(os.path.join(root, f), canonical)
            canonical_files.add(rel_path)

    # Get all files in plugin copy (relative paths)
    plugin_files = set()
    if plugin.exists():
        for root, _, files in os.walk(plugin):
            for f in files:
                rel_path = os.path.relpath(os.path.join(root, f), plugin)
                plugin_files.add(rel_path)

    # Find missing files (in canonical but not in plugin)
    missing_in_plugin = sorted(canonical_files - plugin_files)

    # Find extra files (in plugin but not in canonical)
    extra_in_plugin = sorted(plugin_files - canonical_files)

    # Find differing files (in both but content differs)
    common_files = canonical_files & plugin_files
    for rel_path in sorted(common_files):
        canonical_file = canonical / rel_path
        plugin_file = plugin / rel_path
        if not filecmp.cmp(canonical_file, plugin_file, shallow=False):
            differing_files.append(rel_path)

    return missing_in_plugin, extra_in_plugin, differing_files


def check_drift(canonical: Path, plugin: Path) -> bool:
    """
    Check for drift between canonical and plugin copy.

    Returns:
        True if no drift (all good), False if drift detected.
    """
    missing, extra, differing = compare_directories(canonical, plugin)

    has_drift = bool(missing or differing)

    if has_drift:
        log_fail("DRIFT DETECTED between canonical and plugin-bundled skill")
        print("\n--- Drift Report ---")

        if missing:
            print(f"\nMissing in plugin ({len(missing)} files):")
            for f in missing:
                print(f"  - {f}")

        if differing:
            print(f"\nContent differs ({len(differing)} files):")
            for f in differing:
                print(f"  - {f}")

        if extra:
            log_warn(f"\nExtra files in plugin (not in canonical): {len(extra)}")
            for f in extra:
                print(f"  + {f}")

        print("\n--- Remediation ---")
        print("Run: python scripts/ops/sync_plugin_skills.py --sync")
        return False
    else:
        if extra:
            log_warn(f"Extra files in plugin (not in canonical): {len(extra)}")
            for f in extra:
                print(f"  + {f}")
        log_ok("No drift detected. Canonical and plugin copies are in sync.")
        return True


def sync_skill(canonical: Path, plugin: Path) -> bool:
    """
    Sync canonical skill to plugin-bundled copy.

    Returns:
        True if sync succeeded, False otherwise.
    """
    try:
        # Remove existing plugin skill directory
        if plugin.exists():
            log_info(f"Removing existing plugin copy: {plugin}")
            shutil.rmtree(plugin)

        # Copy canonical to plugin
        log_info(f"Copying canonical → plugin")
        log_info(f"  From: {canonical}")
        log_info(f"  To:   {plugin}")
        shutil.copytree(canonical, plugin)

        log_ok("Sync complete.")
        return True
    except Exception as e:
        log_fail(f"Sync failed: {e}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Sync canonical skill to plugin-bundled copy.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/ops/sync_plugin_skills.py --check   # CI: detect drift
  python scripts/ops/sync_plugin_skills.py --sync    # Dev: fix drift
        """
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true',
                       help='Check for drift (CI mode). Exit non-zero if drift detected.')
    group.add_argument('--sync', action='store_true',
                       help='Sync canonical to plugin (developer mode). Overwrites plugin copy.')

    args = parser.parse_args()

    repo_root = get_repo_root()

    # Define paths
    canonical_skill = repo_root / 'skills' / 'senior-developer-brain'
    plugin_skill = repo_root / 'products' / 'claude-code-plugins' / 'ninobyte-senior-dev-brain' / 'skills' / 'senior-developer-brain'

    # Get version for logging
    version = get_canonical_version(canonical_skill)

    print(f"\n{'='*60}")
    print("Ninobyte Plugin Skill Sync Tool")
    print(f"{'='*60}")
    print(f"Canonical version: {version}")
    print(f"Canonical path:    {canonical_skill}")
    print(f"Plugin path:       {plugin_skill}")
    print(f"Mode:              {'--check (CI)' if args.check else '--sync (Dev)'}")
    print()

    # Validate canonical exists
    if not canonical_skill.exists():
        log_fail(f"Canonical skill not found: {canonical_skill}")
        return 1

    if args.check:
        success = check_drift(canonical_skill, plugin_skill)
        return 0 if success else 1

    elif args.sync:
        success = sync_skill(canonical_skill, plugin_skill)
        if success:
            # Verify after sync
            log_info("Verifying sync...")
            verify_success = check_drift(canonical_skill, plugin_skill)
            return 0 if verify_success else 1
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
