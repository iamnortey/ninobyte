#!/usr/bin/env python3
"""
Ensure Claude Code Marketplace Paths

Validates and repairs Claude Code marketplace path configuration:
- Validates .claude-plugin/marketplace.json JSON syntax
- Enforces plugins[].source starts with "./" (Claude schema requirement)
- Ensures .claude-plugin/products symlink exists and points to ../products
- Validates plugin source paths resolve to existing directories

Usage:
    python3 scripts/ops/ensure_claude_marketplace_paths.py

Exit codes:
    0 - All checks passed
    1 - One or more checks failed (actionable errors provided)

Cross-platform notes:
    - Prefers symlinks when supported (macOS, Linux, Windows with dev mode)
    - Falls back to actionable error if symlinks unsupported
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ANSI colors (disabled if not a TTY)
USE_COLOR = sys.stdout.isatty()


def green(text: str) -> str:
    return f"\033[0;32m{text}\033[0m" if USE_COLOR else text


def red(text: str) -> str:
    return f"\033[0;31m{text}\033[0m" if USE_COLOR else text


def yellow(text: str) -> str:
    return f"\033[0;33m{text}\033[0m" if USE_COLOR else text


def log_ok(msg: str) -> None:
    print(f"{green('✅')} {msg}")


def log_fail(msg: str) -> None:
    print(f"{red('❌')} {msg}")


def log_warn(msg: str) -> None:
    print(f"{yellow('⚠️ ')} {msg}")


def log_info(msg: str) -> None:
    print(f"ℹ️  {msg}")


def get_repo_root() -> Path:
    """Determine repo root from script location."""
    script_path = Path(__file__).resolve()
    # scripts/ops/ensure_claude_marketplace_paths.py -> repo root
    return script_path.parent.parent.parent


def symlinks_supported() -> bool:
    """Check if symlinks are supported on this platform."""
    # On Windows, symlinks require either admin rights or Developer Mode
    if sys.platform == "win32":
        test_dir = Path(__file__).parent
        test_link = test_dir / ".symlink_test"
        test_target = test_dir / ".symlink_target"
        try:
            test_target.touch()
            test_link.symlink_to(test_target)
            test_link.unlink()
            test_target.unlink()
            return True
        except OSError:
            if test_target.exists():
                test_target.unlink()
            return False
    # macOS and Linux support symlinks
    return True


def validate_json_file(path: Path) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    Validate JSON file syntax.
    Returns (success, data_or_none, error_message_or_none).
    """
    if not path.exists():
        return False, None, f"File not found: {path}"

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return True, data, None
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON: {e}"


def validate_source_prefix(plugins: List[dict]) -> Tuple[bool, List[str]]:
    """
    Validate all plugins[].source fields start with "./".
    Returns (all_valid, list_of_errors).
    """
    errors = []
    for i, plugin in enumerate(plugins):
        source = plugin.get("source", "")
        name = plugin.get("name", f"plugin[{i}]")

        if not source:
            errors.append(f"{name}: missing 'source' field")
        elif not source.startswith("./"):
            errors.append(
                f"{name}: source '{source}' must start with './' "
                f"(Claude Code schema requirement)"
            )

    return len(errors) == 0, errors


def ensure_products_symlink(marketplace_dir: Path) -> Tuple[bool, str]:
    """
    Ensure .claude-plugin/products symlink exists and points to ../products.
    Returns (success, status_message).
    """
    products_link = marketplace_dir / "products"
    expected_target = "../products"

    # Check if symlink already exists and is correct
    if products_link.is_symlink():
        actual_target = os.readlink(products_link)
        if actual_target == expected_target:
            return True, f"Symlink valid: {products_link} -> {actual_target}"
        else:
            return False, (
                f"Symlink exists but points to '{actual_target}', "
                f"expected '{expected_target}'. "
                f"Fix: rm {products_link} && ln -sf {expected_target} {products_link}"
            )

    # Check if something else exists at that path
    if products_link.exists():
        return False, (
            f"{products_link} exists but is not a symlink. "
            f"Remove it and create symlink: rm -rf {products_link} && "
            f"ln -sf {expected_target} {products_link}"
        )

    # Symlink doesn't exist, try to create it
    if not symlinks_supported():
        return False, (
            f"Symlink not supported on this platform. "
            f"On Windows, enable Developer Mode or run as admin. "
            f"Required: {products_link} -> {expected_target}"
        )

    try:
        products_link.symlink_to(expected_target)
        return True, f"Created symlink: {products_link} -> {expected_target}"
    except OSError as e:
        return False, f"Failed to create symlink: {e}"


def validate_source_paths(
    marketplace_dir: Path, plugins: List[dict]
) -> Tuple[bool, List[Dict[str, str]]]:
    """
    Validate each plugin source path resolves to an existing directory.
    Returns (all_valid, list_of_plugin_path_info).
    """
    all_valid = True
    path_info = []

    for i, plugin in enumerate(plugins):
        source = plugin.get("source", "")
        name = plugin.get("name", f"plugin[{i}]")

        if not source.startswith("./"):
            # Already caught by validate_source_prefix
            path_info.append(
                {
                    "name": name,
                    "source": source,
                    "resolved": "N/A (invalid prefix)",
                    "exists": False,
                }
            )
            all_valid = False
            continue

        resolved = (marketplace_dir / source).resolve()
        exists = resolved.is_dir()

        path_info.append(
            {
                "name": name,
                "source": source,
                "resolved": str(resolved),
                "exists": exists,
            }
        )

        if not exists:
            all_valid = False

    return all_valid, path_info


def print_proof_of_state(
    marketplace_dir: Path,
    plugins: List[dict],
    path_info: List[Dict[str, str]],
    symlink_status: str,
) -> None:
    """Print structured proof of current state."""
    print("\n" + "=" * 60)
    print("Proof of State")
    print("=" * 60)

    print(f"\nMarketplace base dir: {marketplace_dir}")

    products_link = marketplace_dir / "products"
    if products_link.is_symlink():
        print(f"Symlink: {products_link} -> {os.readlink(products_link)}")
    elif products_link.exists():
        print(f"Symlink: {products_link} (NOT a symlink, error)")
    else:
        print(f"Symlink: {products_link} (missing)")

    print(f"\nPlugins ({len(plugins)}):")
    for info in path_info:
        status = green("EXISTS") if info["exists"] else red("MISSING")
        print(f"  - {info['name']}")
        print(f"    source:   {info['source']}")
        print(f"    resolved: {info['resolved']}")
        print(f"    status:   {status}")

    print("")


def main() -> int:
    """Run all marketplace path checks."""
    repo_root = get_repo_root()
    marketplace_dir = repo_root / ".claude-plugin"
    marketplace_json = marketplace_dir / "marketplace.json"
    plugin_json = (
        repo_root
        / "products"
        / "claude-code-plugins"
        / "ninobyte-senior-dev-brain"
        / ".claude-plugin"
        / "plugin.json"
    )

    print("\n" + "=" * 60)
    print("Claude Code Marketplace Path Setup")
    print("=" * 60)
    print(f"Repo root: {repo_root}")

    all_passed = True

    # Step 1: Validate marketplace directory exists
    print("\n--- Directory Check ---")
    if not marketplace_dir.is_dir():
        log_fail(f"Marketplace directory missing: {marketplace_dir}")
        print(f"    Create it with: mkdir -p {marketplace_dir}")
        return 1
    log_ok(f"Marketplace directory exists: {marketplace_dir}")

    # Step 2: Validate marketplace.json
    print("\n--- JSON Validation ---")
    valid, marketplace_data, error = validate_json_file(marketplace_json)
    if not valid:
        log_fail(f"marketplace.json: {error}")
        all_passed = False
    else:
        log_ok("marketplace.json is valid JSON")

    valid, plugin_data, error = validate_json_file(plugin_json)
    if not valid:
        log_fail(f"plugin.json: {error}")
        all_passed = False
    else:
        log_ok("plugin.json is valid JSON")

    if not all_passed:
        return 1

    # Step 3: Validate source prefix (Claude schema)
    print("\n--- Schema Compliance Check ---")
    plugins = marketplace_data.get("plugins", [])
    valid, errors = validate_source_prefix(plugins)
    if not valid:
        for error in errors:
            log_fail(error)
        all_passed = False
    else:
        log_ok("All plugin sources start with './' (schema compliant)")

    # Step 4: Ensure products symlink
    print("\n--- Symlink Check ---")
    success, symlink_status = ensure_products_symlink(marketplace_dir)
    if success:
        log_ok(symlink_status)
    else:
        log_fail(symlink_status)
        all_passed = False

    # Step 5: Validate resolved paths
    print("\n--- Path Resolution Check ---")
    valid, path_info = validate_source_paths(marketplace_dir, plugins)
    if valid:
        for info in path_info:
            log_ok(f"Plugin source exists: {info['name']} -> {info['resolved']}")
    else:
        for info in path_info:
            if not info["exists"]:
                log_fail(
                    f"Plugin source missing: {info['name']} -> {info['resolved']}"
                )
        all_passed = False

    # Print proof of state
    print_proof_of_state(marketplace_dir, plugins, path_info, symlink_status)

    # Summary
    print("=" * 60)
    if all_passed:
        log_ok("All Claude Code marketplace path checks PASSED")
        return 0
    else:
        log_fail("Some checks FAILED - see errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())

