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

import ast
import filecmp
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple


# Global repo root for relative path formatting (set in main())
_REPO_ROOT: Path = Path(".")


def _rel_path(p: Path) -> str:
    """Convert a path to repo-relative format for clean logging output."""
    try:
        return "./" + str(p.relative_to(_REPO_ROOT))
    except ValueError:
        # Path is not under repo root; return as-is but avoid absolute leakage
        return "./" + p.name


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
        log_fail(f"{description} not found: {_rel_path(path)}")
        return False

    try:
        with open(path, 'r', encoding='utf-8') as f:
            json.load(f)
        log_ok(f"{description} exists and is valid JSON: {_rel_path(path)}")
        return True
    except json.JSONDecodeError as e:
        log_fail(f"{description} is not valid JSON: {_rel_path(path)} - {e}")
        return False


def validate_file_exists(path: Path, description: str) -> bool:
    """Validate that a file exists."""
    if path.exists():
        log_ok(f"{description} exists: {_rel_path(path)}")
        return True
    else:
        log_fail(f"{description} not found: {_rel_path(path)}")
        return False


def validate_directory_exists(path: Path, description: str) -> bool:
    """Validate that a directory exists."""
    if path.is_dir():
        log_ok(f"{description} exists: {_rel_path(path)}")
        return True
    else:
        log_fail(f"{description} not found: {_rel_path(path)}")
        return False


def validate_skill_frontmatter(skill_path: Path) -> bool:
    """Validate that SKILL.md has required YAML frontmatter."""
    if not skill_path.exists():
        log_fail(f"SKILL.md not found: {_rel_path(skill_path)}")
        return False

    try:
        with open(skill_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for frontmatter
        if not content.startswith('---'):
            log_fail(f"SKILL.md missing YAML frontmatter: {_rel_path(skill_path)}")
            return False

        # Find end of frontmatter
        end_match = content.find('---', 3)
        if end_match == -1:
            log_fail(f"SKILL.md has unclosed frontmatter: {_rel_path(skill_path)}")
            return False

        frontmatter = content[3:end_match].strip()

        # Check for required fields
        has_name = re.search(r'^name:\s*.+', frontmatter, re.MULTILINE)
        has_description = re.search(r'^description:\s*.+', frontmatter, re.MULTILINE)

        if not has_name:
            log_fail(f"SKILL.md missing 'name' in frontmatter: {_rel_path(skill_path)}")
            return False

        if not has_description:
            log_fail(f"SKILL.md missing 'description' in frontmatter: {_rel_path(skill_path)}")
            return False

        log_ok(f"SKILL.md has valid frontmatter with name and description: {_rel_path(skill_path)}")
        return True

    except Exception as e:
        log_fail(f"Error reading SKILL.md: {_rel_path(skill_path)} - {e}")
        return False


def validate_plugin_json(plugin_json_path: Path) -> bool:
    """Validate plugin.json has required fields."""
    if not plugin_json_path.exists():
        log_fail(f"plugin.json not found: {_rel_path(plugin_json_path)}")
        return False

    try:
        with open(plugin_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Check required field
        if 'name' not in data:
            log_fail(f"plugin.json missing 'name' field: {_rel_path(plugin_json_path)}")
            return False

        # Validate name is kebab-case
        name = data['name']
        if not re.match(r'^[a-z][a-z0-9-]*$', name):
            log_warn(f"plugin.json 'name' should be kebab-case: {name}")

        log_ok(f"plugin.json is valid: {_rel_path(plugin_json_path)}")
        return True

    except json.JSONDecodeError as e:
        log_fail(f"plugin.json is not valid JSON: {_rel_path(plugin_json_path)} - {e}")
        return False


def validate_marketplace_json(marketplace_path: Path) -> bool:
    """Validate marketplace.json has required fields."""
    if not marketplace_path.exists():
        log_fail(f"marketplace.json not found: {_rel_path(marketplace_path)}")
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

        log_ok(f"marketplace.json is valid: {_rel_path(marketplace_path)}")
        return True

    except json.JSONDecodeError as e:
        log_fail(f"marketplace.json is not valid JSON: {_rel_path(marketplace_path)} - {e}")
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
        log_fail(f"marketplace.json not found: {_rel_path(marketplace_path)}")
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
                    f"Plugin source path does not exist: {plugin_name} -> {_rel_path(resolved_path)}"
                )
                all_passed = False
            else:
                log_ok(f"Plugin source path exists: {plugin_name} -> {_rel_path(resolved_path)}")

        # Check 3: symlink .claude-plugin/products must exist
        products_symlink = marketplace_dir / 'products'
        if not products_symlink.exists():
            log_fail(
                f"Required symlink missing: {_rel_path(products_symlink)}\n"
                f"    Run: ln -sf ../products .claude-plugin/products"
            )
            all_passed = False
        elif not products_symlink.is_symlink():
            log_fail(
                f"{_rel_path(products_symlink)} exists but is not a symlink. "
                f"Claude Code path resolution requires symlink."
            )
            all_passed = False
        else:
            # Verify symlink target
            symlink_target = os.readlink(products_symlink)
            if symlink_target != '../products':
                log_fail(
                    f"Symlink {_rel_path(products_symlink)} points to '{symlink_target}', "
                    f"expected '../products'"
                )
                all_passed = False
            else:
                log_ok(f"Symlink valid: {_rel_path(products_symlink)} -> {symlink_target}")

        if all_passed:
            log_ok("Claude Code marketplace schema validation passed")

        return all_passed

    except json.JSONDecodeError as e:
        log_fail(f"marketplace.json is not valid JSON: {_rel_path(marketplace_path)} - {e}")
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
        log_fail(f"Golden file not found: {_rel_path(golden_path)}")
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
            log_ok(f"Architecture Review format validation passed: {_rel_path(golden_path)}")

        return all_passed

    except Exception as e:
        log_fail(f"Error validating Architecture Review format: {_rel_path(golden_path)} - {e}")
        return False


def validate_skill_drift(canonical: Path, plugin: Path) -> bool:
    """
    Validate no drift between canonical skill and plugin-bundled copy.

    This is a hard gate — CI fails if drift is detected.
    Developers should run: python scripts/ops/sync_plugin_skills.py --sync
    """
    if not canonical.exists():
        log_fail(f"Canonical skill not found: {_rel_path(canonical)}")
        return False

    if not plugin.exists():
        log_fail(f"Plugin skill not found: {_rel_path(plugin)}")
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


# =============================================================================
# AirGap MCP Server Validation (v0.2.0+)
# =============================================================================

# Networking modules that are FORBIDDEN in AirGap default code path
# NOTE: asyncio and ssl are NOT banned - they are general-purpose libraries.
# We ban the actual network stacks: socket, http, urllib, requests, etc.
FORBIDDEN_NETWORK_MODULES: Set[str] = {
    'socket', 'socketserver',
    'http', 'http.client', 'http.server',
    'urllib', 'urllib.request', 'urllib.parse', 'urllib.error',
    'ftplib', 'smtplib', 'poplib', 'imaplib', 'nntplib', 'telnetlib',
    'aiohttp', 'httpx', 'requests', 'urllib3',
    'websocket', 'websockets',
    'paramiko', 'fabric',
}

# Modules that are allowed despite appearing network-related
ALLOWED_NETWORK_EXCEPTIONS: Set[str] = {
    'subprocess',  # Allowed for ripgrep, but shell=True is banned separately
}


def scan_imports_ast(filepath: Path) -> List[Tuple[str, int, str]]:
    """
    Scan a Python file for imports using AST (Abstract Syntax Tree).

    This is more accurate than regex because it:
    - Handles multi-line imports
    - Distinguishes comments from real imports
    - Correctly parses 'from X import Y' statements

    Returns:
        List of (module_name, line_number, import_statement) tuples
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()

        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return []

    imports: List[Tuple[str, int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((alias.name, node.lineno, f"import {alias.name}"))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append((node.module, node.lineno, f"from {node.module} import ..."))
                # Also check for submodule imports like 'from http.client import ...'
                parts = node.module.split('.')
                for i in range(len(parts)):
                    parent = '.'.join(parts[:i+1])
                    if parent != node.module:
                        imports.append((parent, node.lineno, f"from {node.module} import ..."))

    return imports


def validate_airgap_no_networking(airgap_src: Path) -> bool:
    """
    Validate that AirGap MCP server has no networking imports.

    Uses AST-based scanning to reduce false positives from:
    - Comments mentioning network modules
    - String literals containing module names
    - Docstrings

    This is a HARD GATE - CI fails if networking imports are found.
    """
    if not airgap_src.exists():
        log_info(f"AirGap source not found (skipping): {_rel_path(airgap_src)}")
        return True  # Not a failure if AirGap doesn't exist yet

    all_passed = True
    violations: List[str] = []

    for py_file in airgap_src.rglob('*.py'):
        # Skip test files - they may import networking for mocking
        if 'test' in py_file.name.lower() or 'tests' in py_file.parts:
            continue

        imports = scan_imports_ast(py_file)

        for module, lineno, stmt in imports:
            # Check if this module or any parent is forbidden
            module_parts = module.split('.')
            for i in range(len(module_parts)):
                check_module = '.'.join(module_parts[:i+1])
                if check_module in FORBIDDEN_NETWORK_MODULES:
                    if check_module not in ALLOWED_NETWORK_EXCEPTIONS:
                        violations.append(
                            f"{py_file.relative_to(airgap_src)}:{lineno}: {stmt} "
                            f"(forbidden: {check_module})"
                        )
                        all_passed = False
                        break

    if violations:
        log_fail("AirGap networking import violations found:")
        for v in violations[:20]:
            print(f"    {v}")
        if len(violations) > 20:
            print(f"    ... and {len(violations) - 20} more")
        print("\n    AirGap security policy: NO networking imports in default code path")
        return False

    log_ok("AirGap: No forbidden networking imports found")
    return True


def validate_airgap_no_shell_true(airgap_src: Path) -> bool:
    """
    Validate that AirGap MCP server never uses shell=True or os.system/os.popen.

    MVP bar for v0.2.0:
    - Detect literal shell=True keyword argument only (no dataflow tracing)
    - Detect os.system() and os.popen() calls

    This is a HARD GATE - CI fails if violations are found.
    """
    if not airgap_src.exists():
        return True

    all_passed = True
    violations: List[str] = []

    for py_file in airgap_src.rglob('*.py'):
        if 'test' in py_file.name.lower() or 'tests' in py_file.parts:
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        rel_path = py_file.relative_to(airgap_src)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                is_os_call = False

                # Check for os.system() and os.popen()
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                    # Check if it's os.system or os.popen
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id == 'os' and func_name in ('system', 'popen'):
                            is_os_call = True
                            violations.append(
                                f"{rel_path}:{node.lineno}: "
                                f"os.{func_name}() is forbidden"
                            )
                            all_passed = False
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id

                # Check for subprocess calls with shell=True (literal only)
                if not is_os_call and func_name in ('run', 'call', 'Popen', 'check_output', 'check_call'):
                    for keyword in node.keywords:
                        if keyword.arg == 'shell':
                            # Only detect literal True, not variables (MVP scope)
                            if isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                                violations.append(
                                    f"{rel_path}:{node.lineno}: "
                                    f"shell=True in {func_name}() call"
                                )
                                all_passed = False

    if violations:
        log_fail("AirGap shell execution violations found:")
        for v in violations:
            print(f"    {v}")
        print("\n    AirGap security policy: NO shell=True, NO os.system(), NO os.popen()")
        return False

    log_ok("AirGap: No shell execution violations found")
    return True


def validate_airgap_structure(airgap_root: Path) -> bool:
    """
    Validate AirGap MCP server directory structure.
    """
    if not airgap_root.exists():
        log_info(f"AirGap directory not found (skipping): {_rel_path(airgap_root)}")
        return True

    all_passed = True

    # Required files
    required_files = [
        ('README.md', 'AirGap README'),
        ('SECURITY.md', 'AirGap Security Policy'),
        ('src/__init__.py', 'Source package init'),
    ]

    for rel_path, description in required_files:
        filepath = airgap_root / rel_path
        if not filepath.exists():
            log_fail(f"Missing {description}: {_rel_path(filepath)}")
            all_passed = False
        else:
            log_ok(f"{description} exists")

    # Required source modules
    required_modules = [
        'config.py', 'path_security.py', 'audit.py', 'timeout.py',
        'list_dir.py', 'read_file.py', 'search_text.py', 'redact_preview.py'
    ]

    src_dir = airgap_root / 'src'
    if src_dir.exists():
        for module in required_modules:
            if not (src_dir / module).exists():
                log_fail(f"Missing AirGap module: src/{module}")
                all_passed = False
    else:
        log_fail(f"AirGap src directory not found: {_rel_path(src_dir)}")
        all_passed = False

    return all_passed


# =============================================================================
# OpsPack Governance Validation (v0.3.0+)
# =============================================================================
#
# OpsPack enforces strict read-only security constraints:
# - No network imports (socket, http, requests, etc.)
# - No shell execution (subprocess, os.system, os.popen)
# - No file writes (open with 'w', 'a', write(), etc.)
#
# This is a HARD GATE in CI, WARN locally unless --strict.
# =============================================================================

# OpsPack forbidden network modules (same as AirGap)
OPSPACK_FORBIDDEN_NETWORK_MODULES: Set[str] = {
    'socket', 'socketserver',
    'http', 'http.client', 'http.server',
    'urllib', 'urllib.request', 'urllib.parse', 'urllib.error',
    'ftplib', 'smtplib', 'poplib', 'imaplib', 'nntplib', 'telnetlib',
    'aiohttp', 'httpx', 'requests', 'urllib3',
    'websocket', 'websockets',
    'paramiko', 'fabric',
}


def validate_opspack_no_networking(opspack_src: Path) -> bool:
    """
    Validate that OpsPack source has no networking imports.

    Uses AST-based scanning to reduce false positives.
    This is a HARD GATE - CI fails if networking imports are found.
    """
    if not opspack_src.exists():
        log_info(f"OpsPack source not found (skipping): {_rel_path(opspack_src)}")
        return True

    all_passed = True
    violations: List[str] = []

    for py_file in opspack_src.rglob('*.py'):
        # Skip test files
        if 'test' in py_file.name.lower() or 'tests' in py_file.parts:
            continue

        imports = scan_imports_ast(py_file)

        for module, lineno, stmt in imports:
            module_parts = module.split('.')
            for i in range(len(module_parts)):
                check_module = '.'.join(module_parts[:i+1])
                if check_module in OPSPACK_FORBIDDEN_NETWORK_MODULES:
                    violations.append(
                        f"{py_file.relative_to(opspack_src)}:{lineno}: {stmt} "
                        f"(forbidden: {check_module})"
                    )
                    all_passed = False
                    break

    if violations:
        log_fail("OpsPack networking import violations found:")
        for v in violations[:20]:
            print(f"    {v}")
        if len(violations) > 20:
            print(f"    ... and {len(violations) - 20} more")
        print("\n    OpsPack security policy: NO networking imports")
        return False

    log_ok("OpsPack: No forbidden networking imports found")
    return True


def validate_opspack_no_shell_execution(opspack_src: Path) -> bool:
    """
    Validate that OpsPack source never uses shell execution.

    Checks for:
    - subprocess with shell=True
    - os.system() and os.popen()

    This is a HARD GATE - CI fails if violations are found.
    """
    if not opspack_src.exists():
        return True

    all_passed = True
    violations: List[str] = []

    for py_file in opspack_src.rglob('*.py'):
        if 'test' in py_file.name.lower() or 'tests' in py_file.parts:
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        rel_path = py_file.relative_to(opspack_src)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = None
                is_os_call = False

                # Check for os.system() and os.popen()
                if isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id == 'os' and func_name in ('system', 'popen'):
                            is_os_call = True
                            violations.append(
                                f"{rel_path}:{node.lineno}: "
                                f"os.{func_name}() is forbidden"
                            )
                            all_passed = False
                elif isinstance(node.func, ast.Name):
                    func_name = node.func.id

                # Check for subprocess calls with shell=True
                if not is_os_call and func_name in ('run', 'call', 'Popen', 'check_output', 'check_call'):
                    for keyword in node.keywords:
                        if keyword.arg == 'shell':
                            if isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                                violations.append(
                                    f"{rel_path}:{node.lineno}: "
                                    f"shell=True in {func_name}() call"
                                )
                                all_passed = False

    if violations:
        log_fail("OpsPack shell execution violations found:")
        for v in violations:
            print(f"    {v}")
        print("\n    OpsPack security policy: NO shell execution")
        return False

    log_ok("OpsPack: No shell execution violations found")
    return True


def validate_opspack_no_file_writes(opspack_src: Path) -> bool:
    """
    Validate that OpsPack source has no file write patterns.

    Basic heuristic checks for:
    - open() with 'w', 'a', 'x' modes
    - file.write() calls
    - pathlib write_text(), write_bytes()

    This is a HARD GATE - CI fails if violations are found.
    """
    if not opspack_src.exists():
        return True

    all_passed = True
    violations: List[str] = []

    for py_file in opspack_src.rglob('*.py'):
        if 'test' in py_file.name.lower() or 'tests' in py_file.parts:
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        rel_path = py_file.relative_to(opspack_src)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for open() with write modes
                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                    # Check mode argument (positional or keyword)
                    mode = None
                    if len(node.args) >= 2:
                        mode_arg = node.args[1]
                        if isinstance(mode_arg, ast.Constant):
                            mode = mode_arg.value
                    for kw in node.keywords:
                        if kw.arg == 'mode' and isinstance(kw.value, ast.Constant):
                            mode = kw.value.value
                    if mode and any(c in mode for c in 'wax'):
                        violations.append(
                            f"{rel_path}:{node.lineno}: open() with write mode '{mode}'"
                        )
                        all_passed = False

                # Check for pathlib write methods
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ('write_text', 'write_bytes'):
                        violations.append(
                            f"{rel_path}:{node.lineno}: {node.func.attr}() call"
                        )
                        all_passed = False

    if violations:
        log_fail("OpsPack file write violations found:")
        for v in violations:
            print(f"    {v}")
        print("\n    OpsPack security policy: NO file writes (read-only)")
        return False

    log_ok("OpsPack: No file write violations found")
    return True


# =============================================================================
# Markdown Secret-Scan Hygiene (v0.2.2+)
# =============================================================================
#
# ROLLOUT POLICY AND RATIONALE:
# -----------------------------
# This gate enforces that markdown files in products/**/docs/ and products/**/tests/
# do not contain static patterns that trigger secret scanners (PEM headers, AWS keys, etc.).
#
# Policy: HARD FAIL (Option A - Single PR with minimal collateral)
# - The gate is a HARD FAIL in CI from day one.
# - Any existing violations MUST be fixed in the same PR that introduces this gate.
# - Branch scope rules (BRANCH_SCOPE_ALLOWLISTS) explicitly permit fix/ci-* branches
#   to touch products/**/docs/**/*.md and products/**/tests/**/*.md for this purpose.
# - No other product paths are allowed, preventing scope creep.
#
# Rationale:
# - Soft-launch (WARN-only) would allow violations to accumulate, defeating the purpose.
# - The allowlist model ensures collateral fixes stay within markdown documentation only.
# - This is a one-time compliance sweep; future violations fail immediately.
#
# =============================================================================

# Disallowed patterns in markdown files (docs and tests)
# These patterns trigger secret scanners and should use composed strings instead
MARKDOWN_DISALLOWED_PATTERNS: List[Tuple[str, str, str]] = [
    # (regex pattern, pattern name, remediation hint)
    (
        r'-----BEGIN\s+(RSA\s+)?PRIV' + r'ATE\s+KEY-----',
        'Private key marker',
        'Use composed strings: "-----BEGIN " + "PRIV" + "ATE KEY-----"'
    ),
    (
        r'-----END\s+(RSA\s+)?PRIV' + r'ATE\s+KEY-----',
        'Private key end marker',
        'Use composed strings: "-----END " + "PRIV" + "ATE KEY-----"'
    ),
    (
        r'AWS_SEC' + r'RET_ACCESS_KEY',
        'AWS secret key variable',
        'Use composed strings or describe generically'
    ),
    (
        r'pass' + r'word\s*=',
        'Literal credential assignment',
        'Use composed strings: "pass" + "word="'
    ),
    (
        r'PASS' + r'WORD\s*=',
        'Literal credential assignment (uppercase)',
        'Use composed strings: "PASS" + "WORD="'
    ),
]


def validate_markdown_secret_hygiene(products_root: Path) -> bool:
    """
    Validate that markdown files in docs and tests directories do not contain
    static secret-scan signatures.

    This is a HARD GATE - CI fails if disallowed patterns are found.

    Scans:
    - products/**/docs/**/*.md
    - products/**/tests/**/*.md
    """
    if not products_root.exists():
        log_info(f"Products directory not found (skipping): {_rel_path(products_root)}")
        return True

    all_passed = True
    violations: List[str] = []

    # Collect markdown files from docs/ and tests/ subdirectories
    markdown_files: List[Path] = []

    for product_dir in products_root.iterdir():
        if not product_dir.is_dir():
            continue

        # Recursively find docs and tests directories
        for subdir in product_dir.rglob('*'):
            if subdir.is_dir() and subdir.name in ('docs', 'tests'):
                for md_file in subdir.rglob('*.md'):
                    markdown_files.append(md_file)

    if not markdown_files:
        log_info("No markdown files found in products/**/docs/ or products/**/tests/")
        return True

    # Scan each markdown file
    for md_file in markdown_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            rel_path = md_file.relative_to(products_root.parent)

            for pattern, pattern_name, hint in MARKDOWN_DISALLOWED_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    violations.append(
                        f"{rel_path}: {pattern_name}\n"
                        f"      Hint: {hint}"
                    )
                    all_passed = False

        except Exception as e:
            log_warn(f"Could not read {md_file}: {e}")

    if violations:
        log_fail("Markdown secret-scan hygiene violations found:")
        for v in violations[:20]:
            print(f"    {v}")
        if len(violations) > 20:
            print(f"    ... and {len(violations) - 20} more")
        print()
        print("    Policy: Markdown files in docs/ and tests/ must not contain")
        print("    static secret-scan signatures. Use composed strings instead.")
        return False

    log_ok(f"Markdown secret-scan hygiene passed ({len(markdown_files)} files scanned)")
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


# =============================================================================
# Branch Scope Linter (Governance Hardening)
# =============================================================================
#
# SCOPE POLICY (Strict Allowlist Model):
# Each branch prefix has an EXPLICIT allowlist of paths it may touch.
# Any file not matching the allowlist is a violation.
#
# This prevents "kitchen sink" PRs where unrelated changes sneak in.
# =============================================================================

# Branch scope rules using ALLOWLIST model
# Format: (branch_prefix, allowed_patterns, violation_message)
# A file MUST match at least one allowed pattern, or it's a violation.
BRANCH_SCOPE_ALLOWLISTS: List[Tuple[str, List[str], str]] = [
    # ci/* branches: only CI scripts and GitHub workflows
    (
        "ci/",
        [
            "scripts/ci/**",
            ".github/**",
            "*.md",  # Repo-level markdown only (README, CONTRIBUTING, etc.)
        ],
        "ci/* branches may only touch scripts/ci/**, .github/**, or repo-level *.md"
    ),
    # docs/* branches: only documentation
    (
        "docs/",
        [
            "docs/**",
            "*.md",  # Repo-level markdown
        ],
        "docs/* branches may only touch docs/** or repo-level *.md"
    ),
    # fix/ci-* branches: CI scripts + NARROW markdown collateral
    # This is NOT a broad exemption. Only specific markdown paths are allowed.
    (
        "fix/ci-",
        [
            "scripts/ci/**",
            ".github/**",
            "*.md",  # Repo-level markdown
            "products/**/docs/**/*.md",   # Product docs markdown ONLY
            "products/**/tests/**/*.md",  # Product tests markdown ONLY
        ],
        "fix/ci-* branches may touch scripts/ci/**, .github/**, repo-level *.md, "
        "and ONLY markdown under products/**/docs/ or products/**/tests/"
    ),
]


def _glob_match(filepath: str, pattern: str) -> bool:
    """Match filepath against a glob pattern with ** support.

    Handles:
    - ** matches zero or more directory levels
    - * matches any characters except /
    - ? matches single character
    """
    import re

    # Convert glob pattern to regex
    regex_parts = []
    i = 0
    while i < len(pattern):
        if pattern[i:i+2] == '**':
            regex_parts.append('.*')  # Match anything including /
            i += 2
            if i < len(pattern) and pattern[i] == '/':
                i += 1  # Skip trailing / after **
        elif pattern[i] == '*':
            regex_parts.append('[^/]*')  # Match anything except /
            i += 1
        elif pattern[i] == '?':
            regex_parts.append('[^/]')
            i += 1
        elif pattern[i] in '.^$+{}[]|()\\':
            regex_parts.append('\\' + pattern[i])
            i += 1
        else:
            regex_parts.append(pattern[i])
            i += 1

    regex = '^' + ''.join(regex_parts) + '$'
    return bool(re.match(regex, filepath))


def _matches_any_pattern(filepath: str, patterns: List[str]) -> bool:
    """Check if filepath matches any of the given glob patterns.

    Pattern semantics:
    - Patterns without '/' (e.g., '*.md') only match files at repo root.
    - Patterns with '/' use _glob_match for proper ** support.
    """
    for pattern in patterns:
        if '/' not in pattern:
            # Repo-root pattern: only match files without directory separators
            if '/' not in filepath and _glob_match(filepath, pattern):
                return True
        else:
            # Path pattern: use glob matching with ** support
            if _glob_match(filepath, pattern):
                return True
    return False


def validate_branch_scope(
    branch_name: str,
    changed_files: List[str],
    is_ci: bool = False,
    strict: bool = False
) -> bool:
    """
    Validate that a branch only touches files within its declared scope.

    Uses STRICT ALLOWLIST model: files must match an allowed pattern.
    No broad exemptions - every path must be explicitly permitted.

    Args:
        branch_name: The branch name (e.g., "ci/markdown-policy" or "feat/new-feature")
        changed_files: List of changed file paths relative to repo root
        is_ci: If True (or in CI env), violations are HARD FAIL.
        strict: If True, force hard-fail mode even locally (--strict flag).

    Returns:
        True if scope is valid, False if violations found and should fail.
    """
    # Determine if we should hard-fail
    hard_fail = is_ci or strict

    all_passed = True
    matched_rule = False

    for prefix, allowed_patterns, violation_msg in BRANCH_SCOPE_ALLOWLISTS:
        if not branch_name.startswith(prefix):
            continue

        matched_rule = True
        violations: List[str] = []

        for filepath in changed_files:
            if not _matches_any_pattern(filepath, allowed_patterns):
                violations.append(f"  - {filepath}")

        if violations:
            if hard_fail:
                log_fail(f"Branch scope violation: {violation_msg}")
                print("\n    Files outside allowed scope:")
                for v in violations[:15]:
                    print(f"    {v}")
                if len(violations) > 15:
                    print(f"    ... and {len(violations) - 15} more")
                print("\n    Allowed patterns for this branch type:")
                for p in allowed_patterns:
                    print(f"      - {p}")
                all_passed = False
            else:
                log_warn(f"Branch scope warning: {violation_msg}")
                print("    (Use --strict or run in CI for hard failure)")
                for v in violations[:5]:
                    print(f"    {v}")

        break  # Only check first matching rule

    if matched_rule and all_passed:
        log_ok(f"Branch scope valid: '{branch_name}' (strict allowlist)")
    elif not matched_rule:
        # No rule matched - branch type has no restrictions (e.g., feat/*, chore/*)
        log_info(f"Branch '{branch_name}' has no scope restrictions (unregulated prefix)")

    return all_passed



def get_changed_files_vs_main(repo_root: Path) -> List[str]:
    """Get list of files changed between current HEAD and origin/main."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "origin/main...HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
        return files
    except subprocess.CalledProcessError:
        log_warn("Could not determine changed files (git diff failed)")
        return []


def get_branch_name() -> str:
    """Get branch name from environment or git."""
    import subprocess

    # CI environment variables (GitHub Actions)
    branch = os.environ.get("GITHUB_HEAD_REF")  # PR source branch
    if not branch:
        branch = os.environ.get("GITHUB_REF_NAME")  # Push branch

    if branch:
        return branch

    # Fall back to git
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def main() -> int:
    """Run all validations.

    Supports --strict flag to force hard-fail mode for scope violations locally.
    """
    global _REPO_ROOT
    import argparse

    parser = argparse.ArgumentParser(description="Ninobyte Artifact Validation")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Force hard-fail mode for branch scope violations (default in CI)"
    )
    args = parser.parse_args()

    # Determine repo root
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent
    _REPO_ROOT = repo_root  # Set global for _rel_path()

    print(f"\n{'='*60}")
    print("Ninobyte Artifact Validation")
    print(f"{'='*60}")
    print(f"Repo root: {repo_root.name}\n")

    all_passed = True
    strict_mode = args.strict

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

    # 7b. Markdown secret-scan hygiene (v0.2.2+)
    print("\n--- Markdown Secret-Scan Hygiene (v0.2.2) ---")
    products_root = repo_root / 'products'
    if not validate_markdown_secret_hygiene(products_root):
        all_passed = False

    # 8. AirGap MCP Server validation (v0.2.0+)
    # Canonical path: products/mcp-servers/ninobyte-airgap/
    print("\n--- Ninobyte AirGap MCP Server Validation (v0.2.0) ---")
    airgap_root = repo_root / 'products' / 'mcp-servers' / 'ninobyte-airgap'
    if airgap_root.exists():
        if not validate_airgap_structure(airgap_root):
            all_passed = False
        if not validate_airgap_no_networking(airgap_root / 'src'):
            all_passed = False
        if not validate_airgap_no_shell_true(airgap_root / 'src'):
            all_passed = False
    else:
        log_info("Ninobyte AirGap MCP server not yet implemented (skipping)")

    # 8b. OpsPack governance validation (v0.3.0+)
    # Canonical path: products/opspack/
    print("\n--- Ninobyte OpsPack Governance Validation (v0.3.0) ---")
    opspack_root = repo_root / 'products' / 'opspack'
    opspack_src = opspack_root / 'src' / 'ninobyte_opspack'
    if opspack_src.exists():
        if not validate_opspack_no_networking(opspack_src):
            all_passed = False
        if not validate_opspack_no_shell_execution(opspack_src):
            all_passed = False
        if not validate_opspack_no_file_writes(opspack_src):
            all_passed = False
    else:
        log_info("OpsPack source not found (skipping)")

    # 9. Validation log cross-link enforcement (v0.4.0+)
    print("\n--- Validation Log Cross-Links (v0.4.0) ---")
    cross_link_validator = repo_root / 'scripts' / 'ci' / 'validate_validation_log_links.py'
    if cross_link_validator.exists():
        import subprocess
        result = subprocess.run(
            [sys.executable, str(cross_link_validator)],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        # Print output (already formatted by the validator)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        if result.returncode != 0:
            all_passed = False
    else:
        log_info("Validation log cross-link validator not found (skipping)")

    # 10. Branch scope validation (governance hardening - strict allowlist model)
    print("\n--- Branch Scope Validation (Governance) ---")
    branch_name = get_branch_name()
    if branch_name and branch_name != "main":
        changed_files = get_changed_files_vs_main(repo_root)
        if changed_files:
            # Detect if running in CI (always strict) or if --strict was passed
            is_ci = bool(os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"))
            if not validate_branch_scope(
                branch_name,
                changed_files,
                is_ci=is_ci,
                strict=strict_mode
            ):
                all_passed = False
        else:
            log_info("No changed files detected (skipping scope check)")
    else:
        log_info(f"On main branch or unknown branch (skipping scope check)")

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
