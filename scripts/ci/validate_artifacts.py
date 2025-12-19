#!/usr/bin/env python3
"""
Ninobyte Artifact Validation Script

Validates the presence and structure of required artifacts for the Ninobyte
Claude Code plugin marketplace.

Usage:
    python scripts/ci/validate_artifacts.py

Exit codes:
    0 - All validations passed
    1 - One or more validations failed
"""

import filecmp
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


def log_ok(msg: str) -> None:
    print(f"✅ {msg}")


def log_fail(msg: str) -> None:
    print(f"❌ {msg}")


def log_warn(msg: str) -> None:
    print(f"⚠️  {msg}")


def log_info(msg: str) -> None:
    print(f"ℹ️  {msg}")


def validate_json_file(path: Path, description: str) -> bool:
    """Validate that a JSON file exists and is valid JSON."""
    if not path.exists():
        log_fail(f"{description} not found: {path}")
        return False

    try:
        with open(path, 'r', encoding='utf-8') as f:
            json.load(f)
        log_ok(f"{description} exists and is valid JSON: {path}")
        return True
    except json.JSONDecodeError as e:
        log_fail(f"{description} is not valid JSON: {path} - {e}")
        return False


def validate_file_exists(path: Path, description: str) -> bool:
    """Validate that a file exists."""
    if path.exists():
        log_ok(f"{description} exists: {path}")
        return True
    else:
        log_fail(f"{description} not found: {path}")
        return False


def validate_directory_exists(path: Path, description: str) -> bool:
    """Validate that a directory exists."""
    if path.is_dir():
        log_ok(f"{description} exists: {path}")
        return True
    else:
        log_fail(f"{description} not found: {path}")
        return False


def validate_skill_frontmatter(skill_path: Path) -> bool:
    """Validate that SKILL.md has required YAML frontmatter."""
    if not skill_path.exists():
        log_fail(f"SKILL.md not found: {skill_path}")
        return False

    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for frontmatter
        if not content.startswith('---'):
            log_fail(f"SKILL.md missing YAML frontmatter: {skill_path}")
            return False

        # Find end of frontmatter
        end_match = content.find('---', 3)
        if end_match == -1:
            log_fail(f"SKILL.md has unclosed frontmatter: {skill_path}")
            return False

        frontmatter = content[3:end_match].strip()

        # Check for required fields
        has_name = re.search(r'^name:\s*.+', frontmatter, re.MULTILINE)
        has_description = re.search(r'^description:\s*.+', frontmatter, re.MULTILINE)

        if not has_name:
            log_fail(f"SKILL.md missing 'name' in frontmatter: {skill_path}")
            return False

        if not has_description:
            log_fail(f"SKILL.md missing 'description' in frontmatter: {skill_path}")
            return False

        log_ok(f"SKILL.md has valid frontmatter with name and description: {skill_path}")
        return True

    except Exception as e:
        log_fail(f"Error reading SKILL.md: {skill_path} - {e}")
        return False


def validate_plugin_json(plugin_json_path: Path) -> bool:
    """Validate plugin.json has required fields."""
    if not plugin_json_path.exists():
        log_fail(f"plugin.json not found: {plugin_json_path}")
        return False

    try:
        with open(plugin_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check required field
        if 'name' not in data:
            log_fail(f"plugin.json missing 'name' field: {plugin_json_path}")
            return False

        # Validate name is kebab-case
        name = data['name']
        if not re.match(r'^[a-z][a-z0-9-]*$', name):
            log_warn(f"plugin.json 'name' should be kebab-case: {name}")

        log_ok(f"plugin.json is valid: {plugin_json_path}")
        return True

    except json.JSONDecodeError as e:
        log_fail(f"plugin.json is not valid JSON: {plugin_json_path} - {e}")
        return False


def validate_marketplace_json(marketplace_path: Path) -> bool:
    """Validate marketplace.json has required fields."""
    if not marketplace_path.exists():
        log_fail(f"marketplace.json not found: {marketplace_path}")
        return False

    try:
        with open(marketplace_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        errors = []

        if 'name' not in data:
            errors.append("missing 'name' field")

        if 'owner' not in data:
            errors.append("missing 'owner' field")
        elif 'name' not in data.get('owner', {}):
            errors.append("owner missing 'name' field")

        if 'plugins' not in data:
            errors.append("missing 'plugins' field")
        elif not isinstance(data['plugins'], list):
            errors.append("'plugins' must be an array")
        else:
            for i, plugin in enumerate(data['plugins']):
                if 'name' not in plugin:
                    errors.append(f"plugin[{i}] missing 'name'")
                if 'source' not in plugin:
                    errors.append(f"plugin[{i}] missing 'source'")

        if errors:
            for error in errors:
                log_fail(f"marketplace.json: {error}")
            return False

        log_ok(f"marketplace.json is valid: {marketplace_path}")
        return True

    except json.JSONDecodeError as e:
        log_fail(f"marketplace.json is not valid JSON: {marketplace_path} - {e}")
        return False


def validate_claude_code_marketplace_schema(marketplace_path: Path) -> bool:
    """
    Validate Claude Code schema requirements for marketplace.json.

    Claude Code enforces:
    - plugins[].source MUST start with "./"
    - source path must resolve to an existing directory
    - symlink .claude-plugin/products must exist and point to ../products

    See: docs/claude_code_plugin_runbook.md
    """
    if not marketplace_path.exists():
        log_fail(f"marketplace.json not found: {marketplace_path}")
        return False

    marketplace_dir = marketplace_path.parent
    all_passed = True

    try:
        with open(marketplace_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        plugins = data.get('plugins', [])

        for i, plugin in enumerate(plugins):
            source = plugin.get('source', '')
            plugin_name = plugin.get('name', f'plugin[{i}]')

            # Check 1: source must start with "./"
            if not source.startswith('./'):
                log_fail(
                    f"Claude Code schema violation: {plugin_name} source "
                    f"'{source}' must start with './' "
                    f"(Claude Code rejects '../' or bare paths)"
                )
                all_passed = False
                continue

            # Check 2: source path must resolve to existing directory
            resolved_path = (marketplace_dir / source).resolve()
            if not resolved_path.is_dir():
                log_fail(
                    f"Plugin source path does not exist: {plugin_name} -> {resolved_path}"
                )
                all_passed = False
            else:
                log_ok(f"Plugin source path exists: {plugin_name} -> {resolved_path}")

        # Check 3: symlink .claude-plugin/products must exist
        products_symlink = marketplace_dir / 'products'
        if not products_symlink.exists():
            log_fail(
                f"Required symlink missing: {products_symlink}\n"
                f"    Run: ln -sf ../products {products_symlink}"
            )
            all_passed = False
        elif not products_symlink.is_symlink():
            log_fail(
                f"{products_symlink} exists but is not a symlink. "
                f"Claude Code path resolution requires symlink."
            )
            all_passed = False
        else:
            # Verify symlink target
            symlink_target = os.readlink(products_symlink)
            if symlink_target != '../products':
                log_fail(
                    f"Symlink {products_symlink} points to '{symlink_target}', "
                    f"expected '../products'"
                )
                all_passed = False
            else:
                log_ok(f"Symlink valid: {products_symlink} -> {symlink_target}")

        if all_passed:
            log_ok("Claude Code marketplace schema validation passed")

        return all_passed

    except json.JSONDecodeError as e:
        log_fail(f"marketplace.json is not valid JSON: {marketplace_path} - {e}")
        return False
    except Exception as e:
        log_fail(f"Error validating Claude Code schema: {e}")
        return False


def validate_architecture_review_format(golden_path: Path) -> bool:
    """Validate Architecture Review output format in golden files.

    Enforces v0.1.2 "Formatting Determinism" requirements:
    - Required markdown headings with ## / ### tokens
    - Concerns table with exact column structure
    - Risks table with exact column structure
    - CRITICAL flags for known security issues
    """
    if not golden_path.exists():
        log_fail(f"Golden file not found: {golden_path}")
        return False

    try:
        with open(golden_path, 'r', encoding='utf-8') as f:
            content = f.read()

        all_passed = True

        # Required headings (must have ## or ### prefix)
        required_headings = [
            (r'^## Architecture Review:', 'Main heading "## Architecture Review:"'),
            (r'^### Summary', 'Section "### Summary"'),
            (r'^### Components Reviewed', 'Section "### Components Reviewed"'),
            (r'^### Strengths', 'Section "### Strengths"'),
            (r'^### Concerns', 'Section "### Concerns"'),
            (r'^### Security Assessment', 'Section "### Security Assessment"'),
            (r'^### Risks', 'Section "### Risks"'),
            (r'^### Recommendations', 'Section "### Recommendations"'),
            (r'^### Questions for Stakeholders', 'Section "### Questions for Stakeholders"'),
        ]

        for pattern, description in required_headings:
            if not re.search(pattern, content, re.MULTILINE):
                log_fail(f"Missing required heading: {description}")
                all_passed = False

        # Concerns table header validation (exact column structure)
        concerns_table_pattern = r'\|\s*Priority\s*\|\s*Concern\s*\|\s*Impact\s*\|\s*Recommendation\s*\|'
        if not re.search(concerns_table_pattern, content, re.IGNORECASE):
            log_fail("Missing Concerns table header: | Priority | Concern | Impact | Recommendation |")
            all_passed = False
        else:
            log_ok("Concerns table header present")

        # Risks table header validation (exact column structure)
        risks_table_pattern = r'\|\s*Risk\s*\|\s*Likelihood\s*\|\s*Impact\s*\|\s*Mitigation\s*\|'
        if not re.search(risks_table_pattern, content, re.IGNORECASE):
            log_fail("Missing Risks table header: | Risk | Likelihood | Impact | Mitigation |")
            all_passed = False
        else:
            log_ok("Risks table header present")

        # CRITICAL flag validation for known security issues
        critical_issues = [
            (r'CRITICAL.*JWT.*localStorage|JWT.*localStorage.*CRITICAL|localStorage.*JWT.*CRITICAL',
             'JWT stored in localStorage must be flagged as CRITICAL'),
            (r'CRITICAL.*Single.*EC2|Single.*EC2.*CRITICAL|EC2.*instance.*CRITICAL',
             'Single EC2 instance must be flagged as CRITICAL'),
            (r'CRITICAL.*[Ss]hared.*[Dd]atabase|[Ss]hared.*[Dd]atabase.*CRITICAL|[Ss]hared.*PostgreSQL.*CRITICAL',
             'Shared PostgreSQL database must be flagged as CRITICAL'),
        ]

        for pattern, description in critical_issues:
            if not re.search(pattern, content, re.IGNORECASE):
                log_fail(f"Missing CRITICAL flag: {description}")
                all_passed = False

        if all_passed:
            log_ok(f"Architecture Review format validation passed: {golden_path}")

        return all_passed

    except Exception as e:
        log_fail(f"Error validating Architecture Review format: {golden_path} - {e}")
        return False


def validate_skill_drift(canonical: Path, plugin: Path) -> bool:
    """
    Validate no drift between canonical skill and plugin-bundled copy.

    This is a hard gate — CI fails if drift is detected.
    Developers should run: python scripts/ops/sync_plugin_skills.py --sync
    """
    if not canonical.exists():
        log_fail(f"Canonical skill not found: {canonical}")
        return False

    if not plugin.exists():
        log_fail(f"Plugin skill not found: {plugin}")
        return False

    missing_in_plugin: List[str] = []
    differing_files: List[str] = []

    # Get all files in canonical (relative paths)
    canonical_files = set()
    for root_dir, _, files in os.walk(canonical):
        for f in files:
            rel_path = os.path.relpath(os.path.join(root_dir, f), canonical)
            canonical_files.add(rel_path)

    # Get all files in plugin copy (relative paths)
    plugin_files = set()
    for root_dir, _, files in os.walk(plugin):
        for f in files:
            rel_path = os.path.relpath(os.path.join(root_dir, f), plugin)
            plugin_files.add(rel_path)

    # Find missing files (in canonical but not in plugin)
    missing_in_plugin = sorted(canonical_files - plugin_files)

    # Find differing files (in both but content differs)
    common_files = canonical_files & plugin_files
    for rel_path in sorted(common_files):
        canonical_file = canonical / rel_path
        plugin_file = plugin / rel_path
        if not filecmp.cmp(canonical_file, plugin_file, shallow=False):
            differing_files.append(rel_path)

    has_drift = bool(missing_in_plugin or differing_files)

    if has_drift:
        log_fail("DRIFT DETECTED between canonical and plugin-bundled skill")
        print("\n    --- Drift Report ---")

        if missing_in_plugin:
            print(f"\n    Missing in plugin ({len(missing_in_plugin)} files):")
            for f in missing_in_plugin:
                print(f"      - {f}")

        if differing_files:
            print(f"\n    Content differs ({len(differing_files)} files):")
            for f in differing_files:
                print(f"      - {f}")

        print("\n    --- Remediation ---")
        print("    Run: python scripts/ops/sync_plugin_skills.py --sync")
        return False
    else:
        log_ok("No drift between canonical and plugin skill copies")
        return True


def scan_for_secrets(root: Path) -> bool:
    """Scan for potential hardcoded secrets in tracked files."""
    secret_patterns = [
        (r'API_KEY\s*=\s*["\'][^"\']+["\']', 'API_KEY assignment'),
        (r'SECRET\s*=\s*["\'][^"\']+["\']', 'SECRET assignment'),
        (r'PASSWORD\s*=\s*["\'][^"\']+["\']', 'PASSWORD assignment'),
        (r'TOKEN\s*=\s*["\'][^"\']+["\']', 'TOKEN assignment'),
        (r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----', 'Private key'),
    ]

    # File extensions to scan
    scan_extensions = {'.md', '.json', '.js', '.ts', '.py', '.yml', '.yaml', '.sh'}

    # Directories to skip
    skip_dirs = {'.git', 'node_modules', '__pycache__', 'venv', '.venv'}

    issues_found = []

    for filepath in root.rglob('*'):
        if filepath.is_file() and filepath.suffix in scan_extensions:
            # Skip if in excluded directory
            if any(skip_dir in filepath.parts for skip_dir in skip_dirs):
                continue

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                for pattern, description in secret_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # Skip if it's clearly a placeholder or documentation
                        for match in matches:
                            if not any(skip in match.lower() for skip in
                                       ['example', 'placeholder', 'your_', 'xxx', 'todo', '<']):
                                issues_found.append(
                                    f"{filepath}: Potential {description}"
                                )
            except Exception:
                pass  # Skip files that can't be read

    if issues_found:
        log_warn("Potential secrets found (manual review recommended):")
        for issue in issues_found[:10]:  # Limit output
            print(f"    {issue}")
        if len(issues_found) > 10:
            print(f"    ... and {len(issues_found) - 10} more")
        return True  # Warning only, don't fail

    log_ok("No obvious secret patterns found")
    return True


def main() -> int:
    """Run all validations."""
    # Determine repo root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent

    print(f"\n{'='*60}")
    print("Ninobyte Artifact Validation")
    print(f"{'='*60}")
    print(f"Repo root: {repo_root}\n")

    all_passed = True

    # 1. Validate marketplace
    print("\n--- Marketplace Validation ---")
    marketplace_path = repo_root / '.claude-plugin' / 'marketplace.json'
    if not validate_marketplace_json(marketplace_path):
        all_passed = False

    # 1b. Claude Code schema validation (v0.1.3+)
    print("\n--- Claude Code Marketplace Schema (v0.1.3) ---")
    if not validate_claude_code_marketplace_schema(marketplace_path):
        all_passed = False

    # 2. Validate plugin structure
    print("\n--- Plugin Structure Validation ---")
    plugin_root = repo_root / 'products' / 'claude-code-plugins' / 'ninobyte-senior-dev-brain'

    if not validate_directory_exists(plugin_root, "Plugin directory"):
        all_passed = False
    else:
        plugin_json = plugin_root / '.claude-plugin' / 'plugin.json'
        if not validate_plugin_json(plugin_json):
            all_passed = False

        skill_dir = plugin_root / 'skills' / 'senior-developer-brain'
        if not validate_directory_exists(skill_dir, "Plugin skill directory"):
            all_passed = False
        else:
            skill_md = skill_dir / 'SKILL.md'
            if not validate_skill_frontmatter(skill_md):
                all_passed = False

    # 3. Validate canonical skill
    print("\n--- Canonical Skill Validation ---")
    canonical_skill = repo_root / 'skills' / 'senior-developer-brain' / 'SKILL.md'
    if not validate_skill_frontmatter(canonical_skill):
        all_passed = False

    # 4. Validate test artifacts
    print("\n--- Test Artifacts Validation ---")
    fixtures = repo_root / 'skills' / 'senior-developer-brain' / 'tests' / 'fixtures'
    goldens = repo_root / 'skills' / 'senior-developer-brain' / 'tests' / 'goldens'

    if not validate_directory_exists(fixtures, "Test fixtures directory"):
        all_passed = False
    else:
        fixture_files = list(fixtures.glob('*.md'))
        if not fixture_files:
            log_fail("No fixture files found")
            all_passed = False
        else:
            log_ok(f"Found {len(fixture_files)} fixture file(s)")

    if not validate_directory_exists(goldens, "Test goldens directory"):
        all_passed = False
    else:
        golden_files = list(goldens.glob('*.md'))
        if not golden_files:
            log_fail("No golden files found")
            all_passed = False
        else:
            log_ok(f"Found {len(golden_files)} golden file(s)")

    # 5. Validate Architecture Review format in golden files
    print("\n--- Architecture Review Format Validation (v0.1.2) ---")
    golden_001 = goldens / 'golden_001_expected.md'
    if golden_001.exists():
        if not validate_architecture_review_format(golden_001):
            all_passed = False
    else:
        log_warn("golden_001_expected.md not found, skipping format validation")

    # 6. Drift check: canonical vs plugin skill (hard gate)
    print("\n--- Skill Drift Check (v0.1.2) ---")
    canonical_skill_dir = repo_root / 'skills' / 'senior-developer-brain'
    plugin_skill_dir = repo_root / 'products' / 'claude-code-plugins' / 'ninobyte-senior-dev-brain' / 'skills' / 'senior-developer-brain'
    if not validate_skill_drift(canonical_skill_dir, plugin_skill_dir):
        all_passed = False

    # 7. Security scan
    print("\n--- Security Scan ---")
    scan_for_secrets(repo_root)

    # Summary
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ All validations PASSED")
        return 0
    else:
        print("❌ Some validations FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
